export type WorkMode = 'human-led' | 'assisted' | 'autonomous';
export type RolloutStage = 'ongoing' | 1 | 2 | 3 | 4;
export type RolloutJob = { name: string; mode: WorkMode; stage: RolloutStage };
export type RolloutDepartment = { id: string; name: string; summary: string; accent: string; jobs: RolloutJob[] };

const rows = (mode: WorkMode, stage: RolloutStage, names: string): RolloutJob[] =>
  names.split('|').map(name => ({name: name.trim(), mode, stage}));

// These are the owner's proposed job allocations, not FRIDAY execution claims.
// Counts are derived from the named rows; the source captions contain conflicting totals.
export const rolloutDepartments: RolloutDepartment[] = [
  {
    id: 'sales', name: 'Sales', summary: 'Prospecting and campaign design', accent: '#efac86',
    jobs: [
      ...rows('human-led', 'ongoing', 'Offer & positioning|Key-account relationships|Brand-voice & final approvals|Deal strategy on big accounts'),
      ...rows('assisted', 1, 'Lookalike Modeling'),
      ...rows('assisted', 2, 'Trigger Detection'),
      ...rows('assisted', 4, 'Deliverability'),
      ...rows('autonomous', 1, 'ICP Definition|Market Mapping|Database Mining|Web & Maps Scraping|Social Mining|List Building|Contact Enrichment|Email Verification|Account Enrichment|Personalization Research'),
      ...rows('autonomous', 2, 'Fit Scoring'),
      ...rows('autonomous', 3, 'Cold Email Drafting|LinkedIn Messaging|Proof Matching|Cold-Call Scripting|Video Prospecting|Campaign Launch'),
      ...rows('autonomous', 4, 'Campaign Orchestration|Send Optimization'),
    ],
  },
  {
    id: 'deals', name: 'Deals', summary: 'Qualification to signed work', accent: '#f38f98',
    jobs: [
      ...rows('human-led', 'ongoing', 'Closing the Deal|Win/Loss Analysis|Discounting & Concessions|Strategic Account Calls|Proposal Final Sign-Off'),
      ...rows('assisted', 2, 'Objection Library'),
      ...rows('assisted', 3, 'Objection Response|Agreement Drafting'),
      ...rows('assisted', 4, 'Forecasting'),
      ...rows('autonomous', 2, 'Reply Classification|Hot-Lead Routing|Referral Capture|Lead Qualification|Inbox Triage|Call Capture|Post-Call Debrief|CRM Hygiene|Pipeline Reporting'),
      ...rows('autonomous', 3, 'Meeting Booking|Speed-to-Lead|Comment-CTA Fulfillment|Pre-Call Briefing|Follow-Up Drafting|Demo Prototyping|Proposal Generation|Pricing Support'),
      ...rows('autonomous', 4, 'Deal Room Assembly|Reactivation'),
    ],
  },
  {
    id: 'marketing', name: 'Marketing', summary: 'Taste, media and publishing', accent: '#bda3ee',
    jobs: [
      ...rows('human-led', 'ongoing', 'Brand Voice & Taste|Content Strategy & Bets|Sponsor Relationships|Final Publish Approval'),
      ...rows('assisted', 3, 'Image Generation|Thumbnail & Cover Design|Ad Creative|Clip Extraction|Publishing'),
    ],
  },
  {
    id: 'operations', name: 'Operations', summary: 'Delivery, quality and oversight', accent: '#78dfcf',
    jobs: [
      ...rows('human-led', 'ongoing', 'Scope & Trade-off Calls|SOP Generation|Client Trust & Escalations|Architecture Decisions|Final Ship Approval'),
      ...rows('assisted', 1, 'Access Collection|Data Migration'),
      ...rows('assisted', 3, 'Handoff Docs'),
      ...rows('assisted', 4, 'QA & Verification|Agent Evaluation|Monitoring & Alerting|Incident Response'),
    ],
  },
  {
    id: 'intelligence', name: 'Intelligence', summary: 'Evidence about companies and markets', accent: '#8ac9f2',
    jobs: [
      ...rows('human-led', 'ongoing', 'What to research next|Network Mapping|Reading between the lines|Making the warm intro|Trusting the call'),
      ...rows('assisted', 1, 'Buying-Committee Mapping|Warm-Path Finding'),
      ...rows('assisted', 2, 'Account Monitoring|News & Mention Tracking'),
      ...rows('autonomous', 1, 'Company Deep-Dive|Tech-Stack Detection|Funding & Financials Lookup|Person Research|Pricing Research|TAM / Market Sizing'),
      ...rows('autonomous', 2, 'Competitor Teardown|Vertical Analysis|Alert Routing'),
      ...rows('autonomous', 3, 'Research Reports|Data Visualization'),
      ...rows('autonomous', 4, 'Adversarial Verification'),
    ],
  },
  {
    id: 'customer', name: 'Customer', summary: 'Support, retention and community', accent: '#f293b7',
    jobs: [
      ...rows('human-led', 'ongoing', 'Renewal Negotiation|Renewals & Expansion|Strategic Accounts|Member Spotlights|Community Voice|Event Coordination|Save Calls'),
      ...rows('assisted', 2, 'Ticket Triage|Escalations|Health Scoring|Moderation'),
      ...rows('assisted', 3, 'Advocacy & Referrals'),
      ...rows('assisted', 4, 'Churn Prediction'),
      ...rows('autonomous', 3, 'FAQ & Self-Serve|Macro Authoring|QBR Prep|Engagement & Replies'),
      ...rows('autonomous', 4, 'Onboarding Journeys'),
    ],
  },
  {
    id: 'back-office', name: 'Back Office', summary: 'Finance, people and administration', accent: '#ead17e',
    jobs: [
      ...rows('human-led', 'ongoing', 'Hiring Decisions|Entity Compliance|Compliance Sign-Off|Candidate Sourcing|Banking Relationships|Spend Authority'),
      ...rows('assisted', 2, 'Expense Categorization|Contract Lifecycle|Screening & Scheduling'),
      ...rows('assisted', 3, 'HR & Policy Assistant'),
      ...rows('assisted', 4, 'Collections|Cash-Flow Forecasting'),
      ...rows('autonomous', 1, 'Document Filing & Retrieval'),
      ...rows('autonomous', 2, 'Payment Tracking|Revenue Reporting|Budget Tracking|CRM Sync|Email Triage'),
      ...rows('autonomous', 3, 'Invoice Generation|Onboarding & Training'),
      ...rows('autonomous', 4, 'Goal Pacing|Calendar Management'),
    ],
  },
];

export const rolloutStages: Record<Exclude<RolloutStage, 'ongoing'>, {name: string; description: string}> = {
  1: {name: 'Foundation', description: 'Data and the company brain'},
  2: {name: 'Capture', description: 'Classify, extract and score'},
  3: {name: 'Generate', description: 'Produce reviewable work'},
  4: {name: 'Orchestrate', description: 'Agents, monitoring and loops'},
};
