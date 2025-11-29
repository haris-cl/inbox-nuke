# Investigation Report: User's Own Emails Classification Issue

**Date:** 2025-11-29
**Issue:** User's own emails (emails they sent to themselves) were being marked as DELETE/marketing
**Status:** ✅ RESOLVED

---

## Summary

The protection logic for user's own emails was **already working correctly** for all newly scored emails. The issue was **historical data** that was scored before the protection logic was implemented. All 76 affected emails have been migrated and are now correctly classified as KEEP.

---

## Investigation Findings

### 1. Protection Logic (Lines 140-148 in `backend/routers/scoring.py`)

The existing code properly protects user's own emails:

```python
# Override classification if sender is the user's own email
final_classification = score_result.classification
final_score = score_result.total_score
final_reasoning = score_result.reasoning
if user_email and sender_email == user_email:
    final_classification = "KEEP"
    final_score = 0  # Score 0 = highest priority to keep
    final_reasoning = "Classification: KEEP (score: 0/100)\nKey factors:\n  • Email from your own account - always keep"
    logger.info(f"Protected user's own email from {sender_email}")
```

**Verification:**
- ✅ User email is correctly extracted from Gmail API: `hnaeem015@gmail.com`
- ✅ Sender email comparison is case-insensitive (both converted to lowercase)
- ✅ The logic executes successfully for all new emails
- ✅ Logging confirms protection is triggered

### 2. Database Analysis

**Before Migration:**
- Total user emails in database: 117
- KEEP: 41 (recently scored with protection)
- DELETE: 0 ❌ **NO DELETE emails from user - protection working!**
- UNCERTAIN: 76 (scored before protection was added)

**After Migration:**
- Total user emails: 117
- KEEP: 117 ✅ **All protected**
- DELETE: 0
- UNCERTAIN: 0

### 3. Root Cause

The 76 UNCERTAIN emails (mostly with subject "Unsubscribe") were scored **before the protection logic was added** to the codebase. The protection code at lines 140-148 was added later, so these historical emails were never re-processed with the new logic.

**Key Point:** This was NOT a bug in the current code - the protection has been working correctly for all emails scored after it was implemented.

---

## What Was Fixed

### 1. Created Migration Script

**File:** `/Users/hnaeem/inbox-nuke/backend/fix_user_emails.py`

This one-time migration script:
1. Fetches the user's email from Gmail API
2. Finds all emails from the user that are not KEEP
3. Updates them to:
   - Classification: KEEP
   - Score: 0
   - Confidence: 1.0
   - Reasoning: "Email from your own account - always keep"
4. Updates the sender profile for the user's email

### 2. Executed Migration

```bash
cd backend
source venv/bin/activate
python fix_user_emails.py
```

**Results:**
- Updated 76 emails from UNCERTAIN → KEEP
- Updated sender profile for user's email
- All 117 user emails now correctly classified as KEEP

---

## UI Features Already Available

The UI already has functionality to override individual email classifications:

**File:** `frontend/components/email-score-card.tsx` (lines 116-134)

Users can manually override any email's classification using a dropdown:
- Override from UNCERTAIN → KEEP
- Override from DELETE → KEEP
- Override from KEEP → DELETE/UNCERTAIN

The override is saved to the database via the `/api/scoring/emails/{message_id}/override` endpoint.

---

## Prevention Measures

The protection logic is now permanent in the codebase:

1. **During Scoring** (`backend/routers/scoring.py` lines 140-148):
   - Every email is checked against the user's own email address
   - If sender matches user, force KEEP classification with score 0

2. **User Email Extraction** (lines 76-81):
   ```python
   profile = await asyncio.to_thread(
       service.users().getProfile(userId="me").execute
   )
   user_email = profile.get("emailAddress", "").lower()
   ```

3. **Case-Insensitive Comparison** (lines 132, 135, 144):
   ```python
   sender_email = sender_full.split("<")[1].split(">")[0].lower()
   # ...
   if user_email and sender_email == user_email:
   ```

---

## Testing Verification

### Test Case 1: New User Emails
✅ **PASS** - All newly scored user emails are protected with score 0

### Test Case 2: Historical User Emails
✅ **PASS** - After migration, all 117 user emails are KEEP

### Test Case 3: DELETE Classification
✅ **PASS** - Zero DELETE emails from user's own address

### Test Case 4: Sender Profile
✅ **PASS** - User's sender profile updated to classification=KEEP, avg_score=0.0

---

## Recommendations

### 1. Keep Migration Script
Preserve `backend/fix_user_emails.py` for:
- Future reference
- Other users who might have historical data
- Potential similar migrations

### 2. No Code Changes Needed
The protection logic is already correct and working. No changes required to:
- `backend/routers/scoring.py`
- `backend/agent/scoring.py`
- Frontend override functionality

### 3. Monitor Logs
The protection logic logs when it triggers:
```
logger.info(f"Protected user's own email from {sender_email}")
```

Check logs to verify protection is working for new scans.

### 4. Future Considerations
If adding additional protection rules, follow the same pattern:
- Check conditions before final classification
- Override classification, score, and reasoning
- Add appropriate logging
- Set confidence to 1.0 for absolute rules

---

## Files Modified

| File | Type | Description |
|------|------|-------------|
| `/Users/hnaeem/inbox-nuke/backend/fix_user_emails.py` | Created | One-time migration script |
| `/Users/hnaeem/inbox-nuke/backend/data/inbox_nuke.db` | Modified | Updated 76 EmailScore records + 1 SenderProfile |
| `/Users/hnaeem/inbox-nuke/INVESTIGATION_REPORT.md` | Created | This report |

---

## Conclusion

**The issue was NOT a bug in the current code.** The protection logic for user's own emails has been working correctly since it was implemented. The 76 UNCERTAIN emails were historical data from before the protection existed.

**Resolution:** All historical user emails have been migrated to KEEP with score 0. The protection logic remains in place to prevent this issue for all future scans.

**Status:** ✅ **RESOLVED** - No further action required.
