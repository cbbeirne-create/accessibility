/**
 * Team Management Page
 * 
 * Allows Pro users to create teams, invite members, and manage their organization.
 * 
 * Accessibility Features:
 * - Emerald focus rings for keyboard navigation
 * - Proper ARIA labels and roles
 */
import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { 
  Users, Plus, Mail, Trash2, UserMinus, Crown,
  Zap, AlertTriangle, CheckCircle, X, Building2,
  ArrowRight, RefreshCw
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { organizationsAPI } from '../../services/api';
import { formatDate } from '../../utils/wcag';

const TeamPage = () => {
  const { user, refreshUser } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  
  const [organization, setOrganization] = useState(null);
  const [pendingInvites, setPendingInvites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Create team modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTeamName, setNewTeamName] = useState('');
  
  // Invite modal
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');

  // Get invite token from URL if present
  const searchParams = new URLSearchParams(location.search);
  const inviteToken = searchParams.get('invite');

  useEffect(() => {
    fetchData();
    
    // Handle invite token in URL
    if (inviteToken) {
      handleAcceptInviteFromUrl(inviteToken);
    }
  }, [inviteToken]);

  const fetchData = async () => {
    try {
      const [orgData, invitesData] = await Promise.all([
        user?.organization_id ? organizationsAPI.get(user.organization_id) : Promise.resolve(null),
        organizationsAPI.getPendingInvites()
      ]);
      setOrganization(orgData);
      setPendingInvites(invitesData);
    } catch (err) {
      console.error('Failed to fetch team data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptInviteFromUrl = async (token) => {
    setActionLoading(true);
    try {
      await organizationsAPI.acceptInvite(token);
      setSuccess('You have joined the team!');
      await refreshUser();
      navigate('/team', { replace: true });
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to accept invite');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateTeam = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    setError('');

    try {
      await organizationsAPI.create(newTeamName);
      setShowCreateModal(false);
      setNewTeamName('');
      setSuccess('Team created successfully!');
      await refreshUser();
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create team');
    } finally {
      setActionLoading(false);
    }
  };

  const handleInviteMember = async (e) => {
    e.preventDefault();
    if (!organization) return;
    
    setActionLoading(true);
    setError('');

    try {
      await organizationsAPI.inviteMember(organization.id, inviteEmail);
      setShowInviteModal(false);
      setInviteEmail('');
      setSuccess('Invitation sent!');
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send invite');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancelInvite = async (inviteId) => {
    if (!organization) return;
    
    try {
      await organizationsAPI.cancelInvite(organization.id, inviteId);
      setSuccess('Invite cancelled');
      fetchData();
    } catch (err) {
      setError('Failed to cancel invite');
    }
  };

  const handleRemoveMember = async (userId, memberName) => {
    if (!organization) return;
    if (!window.confirm(`Are you sure you want to remove ${memberName} from the team?`)) return;
    
    try {
      await organizationsAPI.removeMember(organization.id, userId);
      setSuccess('Member removed');
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to remove member');
    }
  };

  const handleLeaveTeam = async () => {
    if (!window.confirm('Are you sure you want to leave this team?')) return;
    
    setActionLoading(true);
    try {
      await organizationsAPI.leave();
      setSuccess('You have left the team');
      await refreshUser();
      setOrganization(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to leave team');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteTeam = async () => {
    if (!organization) return;
    if (!window.confirm('Are you sure you want to delete this team? All members will be removed.')) return;
    
    setActionLoading(true);
    try {
      await organizationsAPI.delete(organization.id);
      setSuccess('Team deleted');
      await refreshUser();
      setOrganization(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete team');
    } finally {
      setActionLoading(false);
    }
  };

  const handleAcceptInvite = async (token) => {
    setActionLoading(true);
    try {
      await organizationsAPI.acceptInvite(token);
      setSuccess('You have joined the team!');
      await refreshUser();
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to accept invite');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeclineInvite = async (token) => {
    try {
      await organizationsAPI.declineInvite(token);
      setPendingInvites(pendingInvites.filter(i => i.token !== token));
      setSuccess('Invite declined');
    } catch (err) {
      setError('Failed to decline invite');
    }
  };

  const handleTransferOwnership = async (newOwnerId, memberName) => {
    if (!organization) return;
    if (!window.confirm(`Are you sure you want to transfer ownership to ${memberName}? They must have a Pro plan.`)) return;
    
    setActionLoading(true);
    try {
      await organizationsAPI.transferOwnership(organization.id, newOwnerId);
      setSuccess('Ownership transferred');
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to transfer ownership');
    } finally {
      setActionLoading(false);
    }
  };

  const isPro = user?.plan === 'pro';
  const isOwner = organization?.owner_id === user?.id;

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-400" aria-hidden="true" />
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 py-8 px-4">
      <main id="main-content" className="container mx-auto max-w-4xl" role="main" aria-labelledby="team-heading">
        {/* Header */}
        <div className="flex flex-wrap justify-between items-start gap-4 mb-8">
          <div>
            <h1 id="team-heading" className="text-3xl font-bold text-white mb-2">Team</h1>
            <p className="text-slate-400">
              {organization ? 'Manage your team members and settings' : 'Create or join a team'}
            </p>
          </div>
        </div>

        {/* Alerts */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-300 px-4 py-3 rounded-xl mb-6 flex items-center justify-between" role="alert">
            <span>{error}</span>
            <button onClick={() => setError('')} className="text-red-300 hover:text-red-200">
              <X className="w-5 h-5" aria-hidden="true" />
            </button>
          </div>
        )}
        
        {success && (
          <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 px-4 py-3 rounded-xl mb-6 flex items-center justify-between" role="status">
            <span className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5" aria-hidden="true" />
              <span>{success}</span>
            </span>
            <button onClick={() => setSuccess('')} className="text-emerald-300 hover:text-emerald-200">
              <X className="w-5 h-5" aria-hidden="true" />
            </button>
          </div>
        )}

        {/* Pending Invites (when not in a team) */}
        {!organization && pendingInvites.length > 0 && (
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-2xl p-6 mb-6">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
              <Mail className="w-5 h-5 text-amber-400" aria-hidden="true" />
              <span>Pending Invitations</span>
            </h2>
            <div className="space-y-3">
              {pendingInvites.map((invite) => (
                <div key={invite.id} className="bg-slate-900 rounded-xl p-4 flex items-center justify-between">
                  <div>
                    <p className="text-white font-medium">{invite.organization_name}</p>
                    <p className="text-slate-400 text-sm">
                      Invited by {invite.invited_by_name || 'team owner'}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleAcceptInvite(invite.token)}
                      disabled={actionLoading}
                      className="bg-emerald-500 hover:bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all"
                    >
                      Accept
                    </button>
                    <button
                      onClick={() => handleDeclineInvite(invite.token)}
                      className="bg-slate-700 hover:bg-slate-600 text-slate-300 px-4 py-2 rounded-lg text-sm font-medium transition-all"
                    >
                      Decline
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* No Team State */}
        {!organization && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center">
            <Building2 className="w-16 h-16 text-slate-600 mx-auto mb-4" aria-hidden="true" />
            <h2 className="text-2xl font-semibold text-white mb-2">No Team Yet</h2>
            <p className="text-slate-400 mb-6 max-w-md mx-auto">
              {isPro 
                ? 'Create a team to share scans with your colleagues. Your Pro plan extends to all team members.'
                : 'Teams allow multiple users to share scans and collaborate. Upgrade to Pro to create a team.'
              }
            </p>
            
            {isPro ? (
              <button
                onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center space-x-2 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white px-6 py-3 rounded-xl font-medium transition-all"
              >
                <Plus className="w-5 h-5" aria-hidden="true" />
                <span>Create Team</span>
              </button>
            ) : (
              <Link
                to="/pricing"
                className="inline-flex items-center space-x-2 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white px-6 py-3 rounded-xl font-medium transition-all"
              >
                <Zap className="w-5 h-5" aria-hidden="true" />
                <span>Upgrade to Pro</span>
              </Link>
            )}
          </div>
        )}

        {/* Team View */}
        {organization && (
          <>
            {/* Team Info Card */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-4">
                  <div className="w-14 h-14 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-2xl flex items-center justify-center">
                    <Users className="w-7 h-7 text-white" aria-hidden="true" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-white">{organization.name}</h2>
                    <p className="text-slate-400">{organization.member_count} member{organization.member_count !== 1 ? 's' : ''}</p>
                  </div>
                </div>
                
                {isOwner && (
                  <button
                    onClick={() => setShowInviteModal(true)}
                    className="flex items-center space-x-2 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white px-5 py-2.5 rounded-xl font-medium transition-all"
                  >
                    <Plus className="w-5 h-5" aria-hidden="true" />
                    <span>Invite Member</span>
                  </button>
                )}
              </div>

              {/* Members List */}
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wide">Members</h3>
                {organization.members?.map((member) => (
                  <div key={member.user_id} className="bg-slate-800/50 rounded-xl p-4 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-slate-700 rounded-full flex items-center justify-center">
                        <span className="text-white font-medium">
                          {(member.full_name || member.email)[0].toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="text-white font-medium">{member.full_name || member.email}</span>
                          {member.role === 'owner' && (
                            <span className="flex items-center space-x-1 text-amber-400 text-xs">
                              <Crown className="w-3 h-3" aria-hidden="true" />
                              <span>Owner</span>
                            </span>
                          )}
                          {member.user_id === user?.id && (
                            <span className="text-emerald-400 text-xs">(You)</span>
                          )}
                        </div>
                        <p className="text-slate-400 text-sm">{member.email}</p>
                      </div>
                    </div>
                    
                    {isOwner && member.user_id !== user?.id && (
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleTransferOwnership(member.user_id, member.full_name || member.email)}
                          className="p-2 text-slate-400 hover:text-amber-400 transition-colors rounded-lg hover:bg-slate-700"
                          title="Transfer ownership"
                        >
                          <Crown className="w-5 h-5" aria-hidden="true" />
                        </button>
                        <button
                          onClick={() => handleRemoveMember(member.user_id, member.full_name || member.email)}
                          className="p-2 text-slate-400 hover:text-red-400 transition-colors rounded-lg hover:bg-slate-700"
                          title="Remove member"
                        >
                          <UserMinus className="w-5 h-5" aria-hidden="true" />
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Pending Invites (for owner) */}
              {isOwner && organization.pending_invites?.length > 0 && (
                <div className="mt-6 pt-6 border-t border-slate-700">
                  <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wide mb-3">Pending Invites</h3>
                  <div className="space-y-2">
                    {organization.pending_invites.map((invite) => (
                      <div key={invite.id} className="bg-amber-500/10 rounded-lg p-3 flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Mail className="w-4 h-4 text-amber-400" aria-hidden="true" />
                          <span className="text-slate-300 text-sm">{invite.email}</span>
                          <span className="text-slate-500 text-xs">
                            Expires {formatDate(invite.expires_at)}
                          </span>
                        </div>
                        <button
                          onClick={() => handleCancelInvite(invite.id)}
                          className="text-slate-400 hover:text-red-400 transition-colors"
                          title="Cancel invite"
                        >
                          <X className="w-4 h-4" aria-hidden="true" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Team Actions</h3>
              <div className="space-y-3">
                {isOwner ? (
                  <button
                    onClick={handleDeleteTeam}
                    disabled={actionLoading}
                    className="w-full flex items-center justify-center space-x-2 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 text-red-400 px-4 py-3 rounded-xl font-medium transition-all"
                  >
                    <Trash2 className="w-5 h-5" aria-hidden="true" />
                    <span>Delete Team</span>
                  </button>
                ) : (
                  <button
                    onClick={handleLeaveTeam}
                    disabled={actionLoading}
                    className="w-full flex items-center justify-center space-x-2 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/20 text-amber-400 px-4 py-3 rounded-xl font-medium transition-all"
                  >
                    <UserMinus className="w-5 h-5" aria-hidden="true" />
                    <span>Leave Team</span>
                  </button>
                )}
              </div>
            </div>
          </>
        )}
      </main>

      {/* Create Team Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50" role="dialog" aria-modal="true">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-white mb-4">Create Team</h2>
            
            <form onSubmit={handleCreateTeam} className="space-y-5">
              <div>
                <label htmlFor="team-name" className="block text-sm font-medium text-slate-200 mb-2">
                  Team Name <span className="text-red-400" aria-hidden="true">*</span>
                </label>
                <input
                  type="text"
                  id="team-name"
                  value={newTeamName}
                  onChange={(e) => setNewTeamName(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition-all"
                  placeholder="My Awesome Team"
                  required
                  minLength={2}
                  maxLength={100}
                />
              </div>

              <div className="flex space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 bg-slate-800 hover:bg-slate-700 text-white font-medium py-3 px-4 rounded-xl transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading || !newTeamName.trim()}
                  className="flex-1 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-medium py-3 px-4 rounded-xl transition-all"
                >
                  {actionLoading ? 'Creating...' : 'Create Team'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Invite Member Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50" role="dialog" aria-modal="true">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-white mb-4">Invite Team Member</h2>
            
            <form onSubmit={handleInviteMember} className="space-y-5">
              <div>
                <label htmlFor="invite-email" className="block text-sm font-medium text-slate-200 mb-2">
                  Email Address <span className="text-red-400" aria-hidden="true">*</span>
                </label>
                <input
                  type="email"
                  id="invite-email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition-all"
                  placeholder="colleague@company.com"
                  required
                />
                <p className="text-slate-500 text-sm mt-2">
                  They&apos;ll receive an email invitation to join your team.
                </p>
              </div>

              <div className="flex space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowInviteModal(false)}
                  className="flex-1 bg-slate-800 hover:bg-slate-700 text-white font-medium py-3 px-4 rounded-xl transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading || !inviteEmail.trim()}
                  className="flex-1 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-medium py-3 px-4 rounded-xl transition-all"
                >
                  {actionLoading ? 'Sending...' : 'Send Invite'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeamPage;
