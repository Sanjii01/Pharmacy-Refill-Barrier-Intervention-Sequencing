from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np
import pandas as pd


SEED = 20260706
LABELS = ["A", "B", "C", "D"]

MED_CONTEXTS = {
    "anticoagulant": 18,
    "insulin": 17,
    "transplant_immunosuppressant": 20,
    "seizure_control": 15,
    "heart_failure": 13,
    "asthma_controller": 10,
    "oncology_support": 16,
    "antibiotic_course": 11,
    "hypertension": 6,
    "dermatology": 3,
    "migraine": 5,
    "fertility_support": 8,
}

SETTINGS = [
    "retail_chain_counter",
    "independent_pharmacy",
    "specialty_pharmacy_queue",
    "mail_order_center",
    "hospital_discharge_desk",
    "rural_delivery_route",
]

BARRIERS = {
    "clinical_safety": {
        "weight": 34,
        "phrases": [
            "new dizziness and dose confusion are noted before the refill is released",
            "renal function note conflicts with the current dose on the prescription",
            "the patient reports a possible serious reaction after the last fill",
            "duplicate-therapy wording appears in the transfer note",
        ],
    },
    "no_refills": {
        "weight": 24,
        "phrases": [
            "the prescription has no refills remaining",
            "the prescriber authorization has expired",
            "the refill request was blocked by an exhausted authorization",
            "the chart shows refill quantity zero after the last dispense",
        ],
    },
    "prior_authorization": {
        "weight": 22,
        "phrases": [
            "the claim rejected for prior authorization",
            "payer review is required before the claim can adjudicate",
            "the benefits portal returned a coverage-review stop",
            "a plan exception is required for the next fill",
        ],
    },
    "stock_gap": {
        "weight": 18,
        "phrases": [
            "the usual package size is out of stock",
            "inventory is short at the pickup location",
            "the wholesaler ETA conflicts with the promised pickup time",
            "the store has only a partial package on hand",
        ],
    },
    "cold_chain": {
        "weight": 16,
        "phrases": [
            "cold-chain delivery timing is uncertain",
            "the refrigerated shipment window was missed",
            "temperature-pack staging is not confirmed",
            "the courier scan lacks a refrigerated handoff entry",
        ],
    },
    "affordability": {
        "weight": 14,
        "phrases": [
            "the patient states the copay is unaffordable",
            "the claim posts a high out-of-pocket amount",
            "the assistance card on file is inactive",
            "cash price was requested after benefit rejection",
        ],
    },
    "adherence_side_effect": {
        "weight": 12,
        "phrases": [
            "the patient skipped doses because of side effects",
            "the caregiver reports missed doses after nausea",
            "the refill is late and the note mentions fatigue after dosing",
            "the patient is unsure whether to continue after symptoms",
        ],
    },
    "contact_or_address": {
        "weight": 9,
        "phrases": [
            "the contact number failed verification",
            "the delivery address does not match the profile",
            "the patient has not answered pickup coordination calls",
            "identity verification is incomplete",
        ],
    },
    "lab_monitoring": {
        "weight": 19,
        "phrases": [
            "required monitoring labs are overdue",
            "recent lab values are missing from the referral packet",
            "the protocol requires a current lab before dispensing",
            "monitoring status is older than the clinic threshold",
        ],
    },
}

ACTION_LIBRARY = {
    "safety_clarification": [
        "Call prescriber for dose-safety clarification and document whether dispensing should pause.",
        "Escalate clinical clarification for the conflicting dose or reaction note before release.",
        "Hold final verification and request prescriber guidance on the safety conflict.",
    ],
    "refill_authorization": [
        "Send urgent refill authorization request to the prescriber and check for same-day response.",
        "Open prescriber renewal task for the expired or exhausted prescription.",
        "Request a new prescription before any further fill workflow proceeds.",
    ],
    "benefits_prior_auth": [
        "Start prior authorization or plan-exception workflow with payer-required details.",
        "Route the claim rejection to the benefits team for coverage review.",
        "Prepare payer documentation for the coverage-review stop.",
    ],
    "inventory_resolution": [
        "Check nearby stock, split-package feasibility, or wholesaler ETA before promising pickup.",
        "Route inventory exception to stock resolution and document partial-fill options.",
        "Resolve package-size shortage through transfer, ordering, or partial supply decision.",
    ],
    "cold_chain_delivery": [
        "Rebuild refrigerated courier plan and confirm temperature-pack handoff window.",
        "Coordinate cold-chain shipment staging before the medication leaves the pharmacy.",
        "Verify refrigerated delivery timing and replace missing courier temperature documentation.",
    ],
    "cost_assistance": [
        "Check copay card, foundation, or plan alternative before asking the patient to abandon therapy.",
        "Route high out-of-pocket amount to affordability support and assistance screening.",
        "Update inactive assistance information and reprocess the claim if eligible.",
    ],
    "adherence_counseling": [
        "Schedule pharmacist counseling about missed doses, side effects, and continuation plan.",
        "Call patient or caregiver for adherence support and symptom-management counseling.",
        "Document side-effect concern and counsel before the next pickup or shipment.",
    ],
    "contact_resolution": [
        "Verify patient identity, phone number, and delivery address before outreach is closed.",
        "Resolve failed contact or address mismatch so pickup or shipment can be scheduled.",
        "Update contact details and retry patient coordination.",
    ],
    "lab_followup": [
        "Request missing monitoring labs or clinic confirmation before dispensing.",
        "Pause release until the required lab-monitoring status is confirmed.",
        "Escalate overdue lab requirement to clinic workflow.",
    ],
    "routine_sync": [
        "Offer routine refill synchronization after the blocking issue is resolved.",
        "Add the medication to the next monthly synchronization call.",
        "Move case to routine refill alignment if no blocking issue remains.",
    ],
}

ACTION_MATCH = {
    "clinical_safety": "safety_clarification",
    "no_refills": "refill_authorization",
    "prior_authorization": "benefits_prior_auth",
    "stock_gap": "inventory_resolution",
    "cold_chain": "cold_chain_delivery",
    "affordability": "cost_assistance",
    "adherence_side_effect": "adherence_counseling",
    "contact_or_address": "contact_resolution",
    "lab_monitoring": "lab_followup",
}

SETTING_MODIFIERS = {
    "retail_chain_counter": {"contact_resolution": 2, "inventory_resolution": 3},
    "independent_pharmacy": {"cost_assistance": 2, "refill_authorization": 1},
    "specialty_pharmacy_queue": {"benefits_prior_auth": 3, "cold_chain_delivery": 3, "lab_followup": 2},
    "mail_order_center": {"contact_resolution": 3, "cold_chain_delivery": 2},
    "hospital_discharge_desk": {"refill_authorization": 3, "safety_clarification": 3},
    "rural_delivery_route": {"cold_chain_delivery": 4, "inventory_resolution": 2},
}

RISK_MODIFIERS = {
    "anticoagulant": {"safety_clarification": 5, "lab_followup": 3},
    "insulin": {"cold_chain_delivery": 4, "safety_clarification": 3},
    "transplant_immunosuppressant": {"lab_followup": 5, "refill_authorization": 4, "cold_chain_delivery": 3},
    "seizure_control": {"refill_authorization": 3, "adherence_counseling": 3},
    "heart_failure": {"safety_clarification": 3, "refill_authorization": 2},
    "asthma_controller": {"adherence_counseling": 3},
    "oncology_support": {"benefits_prior_auth": 3, "cost_assistance": 2},
    "antibiotic_course": {"refill_authorization": 2, "adherence_counseling": 2},
}

DIFFICULTY_WORDS = {
    "easy": ["straightforward", "single blocker", "clear next step"],
    "medium": ["mixed blocker", "two-team queue", "ambiguous but actionable"],
    "hard": ["competing blockers", "handoff conflict", "near-tie priority"],
}


def choose_weighted(rng: random.Random, items: dict[str, int]) -> str:
    keys = list(items.keys())
    weights = [items[key] for key in keys]
    return rng.choices(keys, weights=weights, k=1)[0]


def build_case(rng: random.Random, idx: int) -> dict:
    medication_context = choose_weighted(rng, MED_CONTEXTS)
    setting = rng.choice(SETTINGS)
    difficulty = rng.choices(["easy", "medium", "hard"], weights=[0.20, 0.43, 0.37], k=1)[0]
    barrier_count = {"easy": 2, "medium": rng.choice([2, 3]), "hard": rng.choice([3, 4])}[difficulty]

    primary_pool = list(BARRIERS.keys())
    barriers = rng.sample(primary_pool, barrier_count)
    if difficulty == "hard" and "clinical_safety" not in barriers and rng.random() < 0.45:
        barriers[0] = "clinical_safety"
    if medication_context == "transplant_immunosuppressant" and "lab_monitoring" not in barriers and rng.random() < 0.55:
        barriers[-1] = "lab_monitoring"

    barrier_phrases = [rng.choice(BARRIERS[name]["phrases"]) for name in barriers]
    rng.shuffle(barrier_phrases)
    days_gap = rng.choice([0, 1, 2, 3, 5, 7, 10, 14])
    supply_left = rng.choice([0, 1, 2, 3, 5, 8, 14])
    prior_attempts = rng.choice([0, 1, 2, 3])
    caregiver_present = rng.choice(["no caregiver named", "caregiver is coordinating", "clinic nurse is coordinating"])
    queue_age = rng.choice(["same day", "one business day", "three days", "one week"])

    needed_actions = [ACTION_MATCH[barrier] for barrier in barriers]
    decoys = [action for action in ACTION_LIBRARY if action not in needed_actions]
    action_types = list(dict.fromkeys(needed_actions))
    while len(action_types) < 4:
        action_types.append(rng.choice(decoys))
        action_types = list(dict.fromkeys(action_types))
    action_types = action_types[:4]
    rng.shuffle(action_types)

    action_scores = {}
    for action in action_types:
        score = 0.0
        for barrier in barriers:
            if ACTION_MATCH[barrier] == action:
                score += BARRIERS[barrier]["weight"]
        score += SETTING_MODIFIERS.get(setting, {}).get(action, 0)
        score += RISK_MODIFIERS.get(medication_context, {}).get(action, 0)
        if supply_left <= 1 and action in {"refill_authorization", "inventory_resolution", "cold_chain_delivery"}:
            score += 4
        if days_gap >= 7 and action in {"adherence_counseling", "refill_authorization"}:
            score += 3
        if prior_attempts >= 2 and action in {"contact_resolution", "benefits_prior_auth", "refill_authorization"}:
            score += 2
        if difficulty == "hard":
            score = score * 0.82 + rng.uniform(-2.8, 2.8)
        else:
            score += rng.uniform(-1.0, 1.0)
        action_scores[action] = round(score, 4)

    # Keep every row non-degenerate while preserving close hard cases.
    if len(set(action_scores.values())) < 4:
        for offset, action in enumerate(action_types):
            action_scores[action] += offset * 0.17

    label_to_action = dict(zip(LABELS, action_types))
    action_cards = []
    for label, action in label_to_action.items():
        action_cards.append({"action_id": label, "action_text": rng.choice(ACTION_LIBRARY[action])})

    note_parts = [
        f"Medication context: {medication_context.replace('_', ' ')}.",
        f"Workflow setting: {setting.replace('_', ' ')}.",
        f"Case age: {queue_age}; supply remaining: {supply_left} days; refill gap: {days_gap} days.",
        f"Prior outreach attempts: {prior_attempts}; coordination note: {caregiver_present}.",
        "Case note: " + "; ".join(barrier_phrases) + ".",
        f"Queue descriptor: {rng.choice(DIFFICULTY_WORDS[difficulty])}.",
    ]
    rng.shuffle(note_parts)
    case_note = " ".join(note_parts)

    record = {
        "raw_case_id": f"raw_pri_{idx:06d}",
        "pharmacy_setting": setting,
        "medication_context": medication_context,
        "case_note": case_note,
        "action_cards": json.dumps(action_cards, separators=(",", ":")),
        "action_count": 4,
    }
    return record


def main() -> None:
    rng = random.Random(SEED)
    rows = [build_case(rng, idx) for idx in range(7200)]
    data = pd.DataFrame(rows)
    out = Path(__file__).resolve().parent / "data.csv"
    data.to_csv(out, index=False)
    print(f"wrote {len(data):,} rows to {out}")


if __name__ == "__main__":
    main()
