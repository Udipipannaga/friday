"""Record-backed, draft-only operating tools. No external side effects."""
import re
import time
from urllib.parse import urlparse
from sqlalchemy import select
from . import db

TOOLS = frozenset({'match', 'draft_outreach', 'chase_silent', 'draft_invoice', 'weekly_note'})
CARD_LIKE = re.compile(r'(?:\d[ -]?){13,19}')


class DraftBlocked(ValueError):
    pass


def safe_note(value: str) -> str:
    if CARD_LIKE.search(value):
        raise DraftBlocked('Card-like numbers are not allowed in operating records.')
    return value.strip()


def verified_video(person: db.OperatingPerson) -> bool:
    url = urlparse(person.published_video_url)
    return bool(person.video_verified_at and person.published_video_title.strip() and url.scheme == 'https' and url.netloc)


def draft(s, company: db.OperatingCompany, tool: str, person: db.OperatingPerson | None,
          job: db.OperatingJob | None, now: float | None = None) -> tuple[str, dict]:
    """Validate records before composing a bounded draft; never call an action API."""
    now = time.time() if now is None else now
    if tool not in TOOLS:
        raise DraftBlocked('Unknown draft-only tool.')
    if person and person.company_id != company.id or job and job.company_id != company.id:
        raise DraftBlocked('Records belong to another company desk.')
    if person and person.opted_out and tool in ('draft_outreach', 'chase_silent'):
        raise DraftBlocked('This person opted out of outreach.')
    if company.name == 'QuiCut':
        if tool == 'match':
            if not job or not person or person.role != 'editor':
                raise DraftBlocked('A confirmed creator job and editor record are required.')
            return (f'Internal match proposal: consider {person.name} for {job.title}. '
                    'Review the creator brief and editor fit before contacting anyone.',
                    {'job_id': job.id, 'editor_id': person.id, 'customer_visible': False})
        if tool == 'draft_outreach':
            if not person:
                raise DraftBlocked('Read a creator or editor record before drafting outreach.')
            if person.role == 'creator':
                if not verified_video(person):
                    raise DraftBlocked('A verified published video title and HTTPS URL are required.')
                return (f'Hi {person.name}, I watched your published video “{person.published_video_title}” '
                        f'({person.published_video_url}). Would you like to brief QuiCut on one paid cut you want made from it?',
                        {'person_id': person.id, 'video_url': person.published_video_url, 'customer_visible': True})
            if person.role == 'editor':
                if not job or not all((job.creator_confirmation, job.sample_scope, job.sample_fee, job.sample_deadline)):
                    raise DraftBlocked('A real creator job and owner-approved sample scope, fee and deadline are required.')
                return (f'Hi {person.name}, QuiCut has a confirmed creator cut brief. The proposed paid sample is '
                        f'{job.sample_scope}, for {job.sample_fee}, due {job.sample_deadline}. '
                        'Would you like to review the brief? Nothing starts until the terms are agreed.',
                        {'person_id': person.id, 'job_id': job.id, 'customer_visible': True})
            raise DraftBlocked('QuiCut outreach requires a creator or editor record.')
        if tool == 'chase_silent':
            if not person or person.role != 'creator' or not person.open_loop.strip() or not person.last_contact_at:
                raise DraftBlocked('A creator with a recorded open loop and last contact is required.')
            if person.last_contact_at > now - 3 * 86400:
                raise DraftBlocked('Wait three days after the recorded contact before following up.')
            if not verified_video(person):
                raise DraftBlocked('The creator’s published video must be verified.')
            return (f'Hi {person.name}, following up on my note about your published video '
                    f'“{person.published_video_title}.” Is a paid cut still something you want to explore? '
                    'If not, I will close the loop.',
                    {'person_id': person.id, 'last_contact_at': person.last_contact_at, 'customer_visible': True})
        if tool == 'draft_invoice':
            if not job or not job.creator_confirmation or not job.invoice_amount:
                raise DraftBlocked('A confirmed creator job with owner-recorded invoice amount is required.')
            return (f'Invoice draft for owner review — QuiCut job {job.title}. '
                    f'Amount already recorded: {job.invoice_amount}. '
                    'Recipient, payment details, tax treatment and due date: UNKNOWN. Do not send or collect payment.',
                    {'job_id': job.id, 'customer_visible': False, 'money_action': False})
        if tool == 'weekly_note':
            start = now - 7 * 86400
            creators = list(s.scalars(select(db.OperatingPerson).where(
                db.OperatingPerson.company_id == company.id, db.OperatingPerson.role == 'creator',
                db.OperatingPerson.joined_at >= start, db.OperatingPerson.joined_at <= now,
                db.OperatingPerson.join_evidence != '')))
            count = len(creators)
            verdict = 'FAILED WEEK: no new demand-side creator' if count == 0 else 'Creator acquisition recorded'
            return (f'QuiCut weekly note (last 7 days): {count} new creator(s) with owner-recorded join evidence. '
                    f'{verdict}. Next real task: ' + ('draft creator outreach from a verified video record.' if count == 0 else 'review new creator briefs and open loops.'),
                    {'new_creator_ids': [p.id for p in creators], 'customer_visible': False})
    if tool == 'weekly_note':
        return (f'{company.name} weekly note: offer {company.offer}; audience {company.audience}; '
                f'channel {company.channel}; money rules {company.money_rules}. Demand-side acquisition: UNKNOWN.',
                {'customer_visible': False})
    raise DraftBlocked('This company needs owner-supplied operating rules before that draft tool can run.')
