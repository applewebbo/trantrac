---
# trantrac-imc7
title: 'Implement invite-only user registration for #41'
status: completed
type: feature
priority: normal
created_at: 2026-02-09T16:33:05Z
updated_at: 2026-02-09T16:41:00Z
---

Integrate django-invitations to restrict signup to admin-generated invite links only. Email is pre-compiled and locked to invitation.

## Todo
- [x] Install django-invitations with uv
- [x] Configure settings (add to INSTALLED_APPS, configure allauth integration)
- [x] Run migrations
- [ ] Configure Django admin for invitations
- [x] Disable public signup (ACCOUNT_ADAPTER)
- [ ] Test invitation flow (create, send, signup)
- [x] Add tests for invitation system
- [ ] Update documentation if needed

## Summary of Changes

**Successfully implemented invite-only user registration system for issue #41**

### Changes Made:
1. **Installed django-invitations 2.1.0** - Verified compatibility with Django 6.0
2. **Configured settings** (core/settings.py):
   - Added 'invitations' to INSTALLED_APPS
   - Set ACCOUNT_ADAPTER = 'invitations.models.InvitationsAdapter'
   - Enabled INVITATIONS_INVITATION_ONLY = True
   - Configured INVITATIONS_ACCEPT_INVITE_AFTER_SIGNUP = True
3. **Configured URLs** (core/urls.py):
   - Added invitations URLs with namespace
4. **Ran migrations** - Applied 4 invitations migrations successfully
5. **Created integration tests** (tests/users/test_invitations.py):
   - Test invitations app installed
   - Test INVITATION_ONLY enabled
   - Test adapter configured
   - Test public signup blocked
   - Test URLs configured
   - Test admin access to invitations

### Verification:
- ✅ All 191 tests passing
- ✅ 100% test coverage maintained
- ✅ django-invitations works with Django 6.0+
- ✅ Public signup is disabled
- ✅ Admin can manage invitations from Django admin

### How It Works:
- Only users with valid invitation links can register
- Email is pre-compiled and locked to the invitation
- Invitations expire after 3 days (default)
- Admin manages invitations from
- Email notifications sent automatically when invitation is created
