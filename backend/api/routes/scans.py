"""Authenticated scan API routes with shared organization scope and durable queueing."""
import asyncio
import json
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response

from ...core.config import settings
from ...core.database import db
from ...core.security import get_current_user
from ...models.scan import ScanRequest, ScanRequestCreate
from ...models.user import User
from ...services.entitlements import (
    get_authorized_scan,
    release_scan_quota,
    require_pdf_export,
    reserve_scan_quota,
    scan_scope_query,
)
from ...services.external_scanners import runScanWithExternalApi
from ...services.pdf_generator import ReportExporter
from ...services.scan_queue import enqueue_scan_job
from ...services.storage import load_png_bytes
from ...services.url_safety import validate_scan_url

router = APIRouter()
logger = logging.getLogger(__name__)


def _scan_model(data: dict) -> ScanRequest:
    data = dict(data)
    data.pop('_id', None)
    return ScanRequest(**data)


@router.get('/scans', response_model=List[ScanRequest])
async def get_scan_requests(current_user: User = Depends(get_current_user)):
    query = await scan_scope_query(current_user)
    scans = await db.scan_requests.find(query).sort('createdAt', -1).to_list(100)
    return [_scan_model(scan) for scan in scans]


@router.post('/scans', response_model=ScanRequest, status_code=202)
async def create_scan_request(input: ScanRequestCreate, current_user: User = Depends(get_current_user)):
    url = await validate_scan_url(str(input.url))
    await reserve_scan_quota(current_user)
    try:
        scan = ScanRequest(
            url=url,
            tool=input.tool,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
        )
        data = scan.model_dump()
        data['url'] = str(data['url'])
        await db.scan_requests.insert_one(data)
        await enqueue_scan_job(scan.id, url, input.tool.value, current_user.id)
        return scan
    except Exception:
        await release_scan_quota(current_user.id)
        logger.exception('Failed to create queued scan')
        raise HTTPException(status_code=500, detail='Failed to create scan request')


# Static routes are declared before /scans/{scan_id}.
@router.get('/scans/stats')
async def get_scan_stats(current_user: User = Depends(get_current_user)):
    scope = await scan_scope_query(current_user)
    scans = await db.scan_requests.find({**scope, 'status': 'completed'}).sort('createdAt', -1).to_list(500)
    scores = [s['score'] for s in scans if isinstance(s.get('score'), (int, float))]
    history = [{'date': s.get('createdAt'), 'score': s.get('score'), 'url': s.get('url')} for s in scans[:10]][::-1]
    recent_trend = None
    if len(scores) >= 2:
        recent = scores[:3]
        older = scores[-3:]
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        recent_trend = {
            'direction': 'up' if recent_avg > older_avg else 'down' if recent_avg < older_avg else 'stable',
            'recent_average': round(recent_avg, 1),
            'older_average': round(older_avg, 1),
        }
    return {
        'total_scans': len(scans),
        'average_score': round(sum(scores) / len(scores), 1) if scores else 0,
        'best_score': max(scores) if scores else 0,
        'worst_score': min(scores) if scores else 0,
        'unique_urls': len({s.get('url') for s in scans}),
        'score_history': history,
        'recent_trend': recent_trend,
        'score_disclaimer': 'Auditly Accessibility Health Score is an automated indicator, not a WCAG compliance percentage or certification.',
    }


@router.get('/scans/urls')
async def get_scanned_urls(current_user: User = Depends(get_current_user)):
    scope = await scan_scope_query(current_user)
    pipeline = [
        {'$match': {**scope, 'status': 'completed'}},
        {'$sort': {'createdAt': 1}},
        {'$group': {
            '_id': '$url',
            'scan_count': {'$sum': 1},
            'latest_scan': {'$max': '$createdAt'},
            'latest_score': {'$last': '$score'},
            'avg_score': {'$avg': '$score'},
        }},
        {'$sort': {'latest_scan': -1}},
        {'$limit': 50},
    ]
    results = await db.scan_requests.aggregate(pipeline).to_list(50)
    return {'urls': [{
        'url': row['_id'],
        'scan_count': row['scan_count'],
        'latest_scan': row['latest_scan'],
        'latest_score': row.get('latest_score'),
        'avg_score': round(row.get('avg_score') or 0, 1),
    } for row in results], 'total': len(results)}


@router.get('/scans/history/by-url')
async def get_scan_history_by_url(url: str, current_user: User = Depends(get_current_user)):
    scope = await scan_scope_query(current_user)
    normalized = url.rstrip('/')
    scans = await db.scan_requests.find({
        **scope,
        'status': 'completed',
        '$or': [{'url': normalized}, {'url': normalized + '/'}],
    }).sort('createdAt', -1).to_list(100)
    scores = [s['score'] for s in scans if isinstance(s.get('score'), (int, float))]
    trend = None
    if len(scores) >= 2:
        change = scores[0] - scores[1]
        trend = {
            'direction': 'up' if change > 0 else 'down' if change < 0 else 'stable',
            'change': change,
            'change_percent': round(change / scores[1] * 100, 1) if scores[1] else 0,
            'average_score': round(sum(scores) / len(scores), 1),
            'best_score': max(scores),
            'worst_score': min(scores),
            'total_scans': len(scores),
        }
    formatted = [{
        'id': scan.get('id'), 'url': scan.get('url'), 'score': scan.get('score'),
        'status': scan.get('status'), 'createdAt': scan.get('createdAt'), 'tool': scan.get('tool'),
        'issues_summary': {
            'failed': len((scan.get('issues') or {}).get('failed', [])),
            'passed': len((scan.get('issues') or {}).get('passed', [])),
            'incomplete': len((scan.get('issues') or {}).get('incomplete', [])),
        },
    } for scan in scans]
    return {'url': url, 'total_scans': len(formatted), 'scans': formatted, 'trend': trend}


@router.get('/scans/compare/{scan_id_1}/{scan_id_2}')
async def compare_scans(scan_id_1: str, scan_id_2: str, current_user: User = Depends(get_current_user)):
    first = await get_authorized_scan(current_user, scan_id_1)
    second = await get_authorized_scan(current_user, scan_id_2)
    older, newer = (first, second) if first.get('createdAt') <= second.get('createdAt') else (second, first)
    older_issues = (older.get('issues') or {}).get('failed', [])
    newer_issues = (newer.get('issues') or {}).get('failed', [])
    old_by_id = {i.get('id'): i for i in older_issues}
    new_by_id = {i.get('id'): i for i in newer_issues}
    fixed = [old_by_id[k] for k in old_by_id.keys() - new_by_id.keys()]
    added = [new_by_id[k] for k in new_by_id.keys() - old_by_id.keys()]
    unchanged = [new_by_id[k] for k in old_by_id.keys() & new_by_id.keys()]
    old_score = older.get('score') or 0
    new_score = newer.get('score') or 0
    change = new_score - old_score
    return {
        'comparison': {
            'older_scan': {'id': older['id'], 'url': older.get('url'), 'score': old_score, 'createdAt': older.get('createdAt'), 'total_failed': len(older_issues)},
            'newer_scan': {'id': newer['id'], 'url': newer.get('url'), 'score': new_score, 'createdAt': newer.get('createdAt'), 'total_failed': len(newer_issues)},
            'score_change': change,
            'score_change_percent': round(change / old_score * 100, 1) if old_score else 0,
            'improved': change > 0,
        },
        'issues': {
            'fixed': {'count': len(fixed), 'items': fixed[:20]},
            'new': {'count': len(added), 'items': added[:20]},
            'unchanged': {'count': len(unchanged), 'items': unchanged[:20]},
        },
        'summary': {'issues_fixed': len(fixed), 'new_issues': len(added), 'unchanged_issues': len(unchanged), 'net_change': len(fixed) - len(added)},
    }


@router.get('/external-apis/status')
async def get_external_apis_status(current_user: User = Depends(get_current_user)):
    return {
        'wave': {'configured': bool(settings.WAVE_API_KEY)},
        'equalweb': {'configured': bool(settings.EQUALWEB_API_KEY)},
        'accessibe': {'configured': bool(settings.ACCESSIBE_API_KEY)},
    }


@router.get('/scans/{scan_id}', response_model=ScanRequest)
async def get_scan_request(scan_id: str, current_user: User = Depends(get_current_user)):
    return _scan_model(await get_authorized_scan(current_user, scan_id))


@router.delete('/scans/{scan_id}')
async def delete_scan_request(scan_id: str, current_user: User = Depends(get_current_user)):
    query = {'id': scan_id, **(await scan_scope_query(current_user))}
    result = await db.scan_requests.delete_one(query)
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail='Scan not found')
    await db.scan_jobs.delete_many({'scan_id': scan_id, 'status': 'queued'})
    return {'message': 'Scan deleted successfully'}


@router.get('/scans/{scan_id}/export/pdf')
async def export_scan_pdf(scan_id: str, current_user: User = Depends(get_current_user)):
    await require_pdf_export(current_user)
    scan = await get_authorized_scan(current_user, scan_id)
    pdf = await ReportExporter.generate_pdf_report(scan)
    filename = f"auditly_accessibility_report_{scan_id[:8]}.pdf"
    return Response(content=pdf, media_type='application/pdf', headers={'Content-Disposition': f'attachment; filename="{filename}"'})


@router.get('/scans/{scan_id}/export/json')
async def export_scan_json(scan_id: str, current_user: User = Depends(get_current_user)):
    scan = await get_authorized_scan(current_user, scan_id)
    report = await ReportExporter.generate_json_report(scan)
    filename = f"auditly_accessibility_data_{scan_id[:8]}.json"
    return Response(content=json.dumps(report, indent=2, default=str), media_type='application/json', headers={'Content-Disposition': f'attachment; filename="{filename}"'})


@router.get('/scans/{scan_id}/screenshot')
async def get_scan_screenshot(scan_id: str, current_user: User = Depends(get_current_user)):
    scan = await get_authorized_scan(current_user, scan_id)
    image = await asyncio.to_thread(
        load_png_bytes,
        base64_data=scan.get('full_page_screenshot'),
        key=scan.get('full_page_screenshot_key'),
    )
    if not image:
        raise HTTPException(status_code=404, detail='Screenshot not available')
    return Response(content=image, media_type='image/png', headers={'Content-Disposition': f'inline; filename="scan_{scan_id[:8]}.png"'})


@router.post('/scans/{scan_id}/run-external')
async def run_external_api_scan(scan_id: str, current_user: User = Depends(get_current_user)):
    scan = await get_authorized_scan(current_user, scan_id)
    if scan.get('tool') == 'axe-core':
        raise HTTPException(status_code=400, detail='This scan is configured for axe-core, not an external scanner.')
    result = await runScanWithExternalApi(scan_id)
    if not result.get('success'):
        raise HTTPException(status_code=502, detail='External accessibility scanner failed.')
    return {'message': 'External API scan completed', 'scan_id': scan_id, 'score': result.get('score'), 'tool': result.get('tool')}
