"""
Organization/Team API routes.
Handles team creation, member management, and invites.
"""
import logging
import secrets
from datetime import datetime, timezone, timedelta
from typing import List

from fastapi import APIRouter, HTTPException, Depends

from ...core.database import db
from ...core.security import get_current_user
from ...models.user import User, UserPlan
from ...models.organization import (
    Organization,
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationMember,
    OrganizationMemberInfo,
    OrganizationInvite,
    OrganizationInviteCreate,
    OrganizationInviteInfo,
    OrganizationWithMembers,
    OrganizationProfile,
    OrganizationRole,
    TransferOwnershipRequest
)
from ...services.email_service import send_team_invite_email

router = APIRouter(prefix="/organizations")
logger = logging.getLogger(__name__)


def generate_invite_token() -> str:
    """Generate a secure invite token."""
    return secrets.token_urlsafe(32)


async def get_user_organization_role(user_id: str, org_id: str) -> OrganizationRole | None:
    """Get user's role in an organization."""
    member = await db.organization_members.find_one({
        "organization_id": org_id,
        "user_id": user_id
    })
    return OrganizationRole(member["role"]) if member else None


async def is_organization_owner(user_id: str, org_id: str) -> bool:
    """Check if user is the owner of an organization."""
    role = await get_user_organization_role(user_id, org_id)
    return role == OrganizationRole.owner


async def get_effective_plan(user: User) -> UserPlan:
    """
    Get user's effective plan considering team membership.
    If user is in an org, they inherit the owner's plan.
    """
    if not user.organization_id:
        return user.plan
    
    # Get organization owner's plan
    org = await db.organizations.find_one({"id": user.organization_id})
    if not org:
        return user.plan
    
    owner = await db.users.find_one({"id": org["owner_id"]})
    if not owner:
        return user.plan
    
    return UserPlan(owner.get("plan", "free"))


@router.get("/current", response_model=OrganizationProfile | None)
async def get_current_organization(current_user: User = Depends(get_current_user)):
    """Get the user's current organization."""
    if not current_user.organization_id:
        return None
    
    org = await db.organizations.find_one({"id": current_user.organization_id})
    if not org:
        return None
    
    role = await get_user_organization_role(current_user.id, org["id"])
    member_count = await db.organization_members.count_documents({"organization_id": org["id"]})
    
    return OrganizationProfile(
        id=org["id"],
        name=org["name"],
        role=role,
        owner_id=org["owner_id"],
        member_count=member_count,
        is_owner=org["owner_id"] == current_user.id
    )


@router.post("", response_model=Organization)
async def create_organization(
    input: OrganizationCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new organization. Pro users only."""
    try:
        # Check if user is Pro
        if current_user.plan != UserPlan.pro:
            raise HTTPException(
                status_code=403,
                detail="Only Pro users can create teams. Upgrade to Pro to create a team."
            )
        
        # Check if user already belongs to an organization
        if current_user.organization_id:
            raise HTTPException(
                status_code=400,
                detail="You already belong to a team. Leave your current team to create a new one."
            )
        
        now = datetime.now(timezone.utc)
        
        # Create organization
        org = Organization(
            name=input.name,
            owner_id=current_user.id,
            created_at=now,
            updated_at=now
        )
        
        await db.organizations.insert_one(org.dict())
        
        # Add owner as member
        owner_member = OrganizationMember(
            organization_id=org.id,
            user_id=current_user.id,
            role=OrganizationRole.owner,
            joined_at=now
        )
        await db.organization_members.insert_one(owner_member.dict())
        
        # Update user's organization_id
        await db.users.update_one(
            {"id": current_user.id},
            {"$set": {"organization_id": org.id}}
        )
        
        logger.info(f"Organization {org.id} created by user {current_user.id}")
        return org
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating organization: {e}")
        raise HTTPException(status_code=500, detail="Failed to create team")


@router.get("/{org_id}", response_model=OrganizationWithMembers)
async def get_organization(
    org_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get organization details with members."""
    try:
        # Check user belongs to this org
        if current_user.organization_id != org_id:
            raise HTTPException(status_code=403, detail="You are not a member of this team")
        
        org = await db.organizations.find_one({"id": org_id})
        if not org:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Get members with user details
        members = []
        member_docs = await db.organization_members.find({"organization_id": org_id}).to_list(100)
        
        for member in member_docs:
            user = await db.users.find_one({"id": member["user_id"]})
            if user:
                members.append(OrganizationMemberInfo(
                    user_id=user["id"],
                    email=user["email"],
                    full_name=user.get("full_name"),
                    role=OrganizationRole(member["role"]),
                    joined_at=member["joined_at"]
                ))
        
        # Get pending invites (owner only)
        pending_invites = []
        if org["owner_id"] == current_user.id:
            invite_docs = await db.organization_invites.find({
                "organization_id": org_id,
                "expires_at": {"$gt": datetime.now(timezone.utc)}
            }).to_list(50)
            
            for invite in invite_docs:
                inviter = await db.users.find_one({"id": invite["invited_by"]})
                pending_invites.append(OrganizationInviteInfo(
                    id=invite["id"],
                    email=invite["email"],
                    organization_name=org["name"],
                    invited_by_name=inviter.get("full_name") if inviter else None,
                    expires_at=invite["expires_at"],
                    created_at=invite["created_at"]
                ))
        
        return OrganizationWithMembers(
            id=org["id"],
            name=org["name"],
            owner_id=org["owner_id"],
            members=members,
            pending_invites=pending_invites,
            member_count=len(members),
            created_at=org["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching organization {org_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch team details")


@router.put("/{org_id}", response_model=Organization)
async def update_organization(
    org_id: str,
    update_data: OrganizationUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update organization. Owner only."""
    try:
        # Check ownership
        if not await is_organization_owner(current_user.id, org_id):
            raise HTTPException(status_code=403, detail="Only the team owner can update team settings")
        
        update_dict = {"updated_at": datetime.now(timezone.utc)}
        if update_data.name is not None:
            update_dict["name"] = update_data.name
        
        await db.organizations.update_one({"id": org_id}, {"$set": update_dict})
        
        updated = await db.organizations.find_one({"id": org_id})
        return Organization(**updated)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating organization {org_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update team")


@router.delete("/{org_id}")
async def delete_organization(
    org_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete organization. Owner only. All members will be removed."""
    try:
        # Check ownership
        if not await is_organization_owner(current_user.id, org_id):
            raise HTTPException(status_code=403, detail="Only the team owner can delete the team")
        
        # Get all members
        members = await db.organization_members.find({"organization_id": org_id}).to_list(1000)
        member_ids = [m["user_id"] for m in members]
        
        # Remove organization_id from all members
        await db.users.update_many(
            {"id": {"$in": member_ids}},
            {"$set": {"organization_id": None}}
        )
        
        # Delete all members
        await db.organization_members.delete_many({"organization_id": org_id})
        
        # Delete all invites
        await db.organization_invites.delete_many({"organization_id": org_id})
        
        # Delete organization
        await db.organizations.delete_one({"id": org_id})
        
        # Update scans to remove org association (keep scans but mark as orphaned)
        await db.scan_requests.update_many(
            {"organization_id": org_id},
            {"$set": {"organization_id": None}}
        )
        
        logger.info(f"Organization {org_id} deleted by owner {current_user.id}")
        return {"message": "Team deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting organization {org_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete team")


@router.post("/{org_id}/invite", response_model=OrganizationInviteInfo)
async def invite_member(
    org_id: str,
    invite_data: OrganizationInviteCreate,
    current_user: User = Depends(get_current_user)
):
    """Invite a new member to the organization. Owner only."""
    try:
        # Check ownership
        if not await is_organization_owner(current_user.id, org_id):
            raise HTTPException(status_code=403, detail="Only the team owner can invite members")
        
        org = await db.organizations.find_one({"id": org_id})
        if not org:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Check if user is already a member
        existing_user = await db.users.find_one({"email": invite_data.email})
        if existing_user and existing_user.get("organization_id") == org_id:
            raise HTTPException(status_code=400, detail="This user is already a member of your team")
        
        if existing_user and existing_user.get("organization_id"):
            raise HTTPException(status_code=400, detail="This user already belongs to another team")
        
        # Check if invite already exists
        existing_invite = await db.organization_invites.find_one({
            "organization_id": org_id,
            "email": invite_data.email,
            "expires_at": {"$gt": datetime.now(timezone.utc)}
        })
        if existing_invite:
            raise HTTPException(status_code=400, detail="An active invite already exists for this email")
        
        now = datetime.now(timezone.utc)
        
        # Create invite
        invite = OrganizationInvite(
            organization_id=org_id,
            email=invite_data.email,
            token=generate_invite_token(),
            invited_by=current_user.id,
            expires_at=now + timedelta(days=7),
            created_at=now
        )
        
        await db.organization_invites.insert_one(invite.dict())
        
        # Send invite email
        await send_team_invite_email(
            invite_data.email,
            org["name"],
            current_user.full_name or current_user.email,
            invite.token
        )
        
        logger.info(f"Invite sent to {invite_data.email} for org {org_id}")
        
        return OrganizationInviteInfo(
            id=invite.id,
            email=invite.email,
            organization_name=org["name"],
            invited_by_name=current_user.full_name,
            expires_at=invite.expires_at,
            created_at=invite.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inviting member: {e}")
        raise HTTPException(status_code=500, detail="Failed to send invite")


@router.delete("/{org_id}/invites/{invite_id}")
async def cancel_invite(
    org_id: str,
    invite_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel a pending invite. Owner only."""
    try:
        if not await is_organization_owner(current_user.id, org_id):
            raise HTTPException(status_code=403, detail="Only the team owner can cancel invites")
        
        result = await db.organization_invites.delete_one({
            "id": invite_id,
            "organization_id": org_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Invite not found")
        
        return {"message": "Invite cancelled"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling invite: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel invite")


@router.get("/invites/pending", response_model=List[OrganizationInviteInfo])
async def get_pending_invites(current_user: User = Depends(get_current_user)):
    """Get pending invites for the current user's email."""
    try:
        invites = await db.organization_invites.find({
            "email": current_user.email,
            "expires_at": {"$gt": datetime.now(timezone.utc)}
        }).to_list(10)
        
        result = []
        for invite in invites:
            org = await db.organizations.find_one({"id": invite["organization_id"]})
            inviter = await db.users.find_one({"id": invite["invited_by"]})
            
            if org:
                result.append(OrganizationInviteInfo(
                    id=invite["id"],
                    email=invite["email"],
                    organization_name=org["name"],
                    invited_by_name=inviter.get("full_name") if inviter else None,
                    expires_at=invite["expires_at"],
                    created_at=invite["created_at"]
                ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching pending invites: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch invites")


@router.post("/invites/{token}/accept")
async def accept_invite(
    token: str,
    current_user: User = Depends(get_current_user)
):
    """Accept an organization invite."""
    try:
        # Check if user already in an org
        if current_user.organization_id:
            raise HTTPException(
                status_code=400, 
                detail="You already belong to a team. Leave your current team first."
            )
        
        # Find invite
        invite = await db.organization_invites.find_one({
            "token": token,
            "email": current_user.email,
            "expires_at": {"$gt": datetime.now(timezone.utc)}
        })
        
        if not invite:
            raise HTTPException(status_code=404, detail="Invalid or expired invite")
        
        org_id = invite["organization_id"]
        now = datetime.now(timezone.utc)
        
        # Add user as member
        member = OrganizationMember(
            organization_id=org_id,
            user_id=current_user.id,
            role=OrganizationRole.member,
            joined_at=now
        )
        await db.organization_members.insert_one(member.dict())
        
        # Update user's organization_id
        await db.users.update_one(
            {"id": current_user.id},
            {"$set": {"organization_id": org_id}}
        )
        
        # Delete the invite
        await db.organization_invites.delete_one({"id": invite["id"]})
        
        org = await db.organizations.find_one({"id": org_id})
        
        logger.info(f"User {current_user.id} joined organization {org_id}")
        return {"message": f"You have joined {org['name']}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting invite: {e}")
        raise HTTPException(status_code=500, detail="Failed to accept invite")


@router.post("/invites/{token}/decline")
async def decline_invite(
    token: str,
    current_user: User = Depends(get_current_user)
):
    """Decline an organization invite."""
    try:
        result = await db.organization_invites.delete_one({
            "token": token,
            "email": current_user.email
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Invite not found")
        
        return {"message": "Invite declined"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error declining invite: {e}")
        raise HTTPException(status_code=500, detail="Failed to decline invite")


@router.delete("/{org_id}/members/{user_id}")
async def remove_member(
    org_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove a member from the organization. Owner only."""
    try:
        # Check ownership
        if not await is_organization_owner(current_user.id, org_id):
            raise HTTPException(status_code=403, detail="Only the team owner can remove members")
        
        # Can't remove yourself (owner)
        if user_id == current_user.id:
            raise HTTPException(status_code=400, detail="Owner cannot remove themselves. Transfer ownership first or delete the team.")
        
        # Check if user is a member
        member = await db.organization_members.find_one({
            "organization_id": org_id,
            "user_id": user_id
        })
        
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        
        # Remove membership
        await db.organization_members.delete_one({"id": member["id"]})
        
        # Update user's organization_id
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"organization_id": None}}
        )
        
        logger.info(f"User {user_id} removed from organization {org_id}")
        return {"message": "Member removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing member: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove member")


@router.post("/leave")
async def leave_organization(current_user: User = Depends(get_current_user)):
    """Leave the current organization. Members only (owner must transfer ownership first)."""
    try:
        if not current_user.organization_id:
            raise HTTPException(status_code=400, detail="You are not a member of any team")
        
        org_id = current_user.organization_id
        
        # Check if user is owner
        if await is_organization_owner(current_user.id, org_id):
            raise HTTPException(
                status_code=400, 
                detail="As the owner, you must transfer ownership before leaving, or delete the team."
            )
        
        # Remove membership
        await db.organization_members.delete_one({
            "organization_id": org_id,
            "user_id": current_user.id
        })
        
        # Update user's organization_id
        await db.users.update_one(
            {"id": current_user.id},
            {"$set": {"organization_id": None}}
        )
        
        logger.info(f"User {current_user.id} left organization {org_id}")
        return {"message": "You have left the team"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error leaving organization: {e}")
        raise HTTPException(status_code=500, detail="Failed to leave team")


@router.post("/{org_id}/transfer-ownership")
async def transfer_ownership(
    org_id: str,
    request: TransferOwnershipRequest,
    current_user: User = Depends(get_current_user)
):
    """Transfer organization ownership to another member. Owner only."""
    try:
        # Check ownership
        if not await is_organization_owner(current_user.id, org_id):
            raise HTTPException(status_code=403, detail="Only the team owner can transfer ownership")
        
        new_owner_id = request.new_owner_id
        
        # Can't transfer to yourself
        if new_owner_id == current_user.id:
            raise HTTPException(status_code=400, detail="You are already the owner")
        
        # Check new owner is a member
        new_owner_member = await db.organization_members.find_one({
            "organization_id": org_id,
            "user_id": new_owner_id
        })
        
        if not new_owner_member:
            raise HTTPException(status_code=404, detail="User is not a member of this team")
        
        # Check new owner is Pro (required to maintain team)
        new_owner = await db.users.find_one({"id": new_owner_id})
        if not new_owner or new_owner.get("plan") != "pro":
            raise HTTPException(
                status_code=400, 
                detail="New owner must have a Pro plan to own a team"
            )
        
        now = datetime.now(timezone.utc)
        
        # Update organization owner
        await db.organizations.update_one(
            {"id": org_id},
            {"$set": {"owner_id": new_owner_id, "updated_at": now}}
        )
        
        # Update member roles
        await db.organization_members.update_one(
            {"organization_id": org_id, "user_id": current_user.id},
            {"$set": {"role": OrganizationRole.member}}
        )
        await db.organization_members.update_one(
            {"organization_id": org_id, "user_id": new_owner_id},
            {"$set": {"role": OrganizationRole.owner}}
        )
        
        logger.info(f"Ownership of org {org_id} transferred from {current_user.id} to {new_owner_id}")
        return {"message": "Ownership transferred successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transferring ownership: {e}")
        raise HTTPException(status_code=500, detail="Failed to transfer ownership")
