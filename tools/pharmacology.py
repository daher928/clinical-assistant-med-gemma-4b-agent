"""
Pharmacology knowledge tool for drug mechanism, pharmacokinetics, and pharmacodynamics queries.

This tool provides pharmacology information from medical literature and knowledge bases
to support safety monitoring and drug interaction analysis.
"""
import json
import os
import asyncio
import random
from typing import Dict, List, Optional
from config import Config
from tools.base import BaseTool


# Pharmacology knowledge base (in a real system, this would be from a comprehensive database)
PHARMACOLOGY_KB = {
    "metformin": {
        "mechanism": "Biguanide that decreases hepatic glucose production via AMPK activation, decreases intestinal glucose absorption, and increases peripheral glucose uptake. Does not stimulate insulin secretion.",
        "pharmacokinetics": {
            "absorption": "Well absorbed from GI tract, bioavailability ~50-60%",
            "distribution": "Minimal protein binding, distributed to tissues",
            "metabolism": "Not metabolized by liver",
            "elimination": "Renally cleared, half-life ~6 hours",
            "clearance": "eGFR-dependent clearance, accumulates in renal impairment"
        },
        "pharmacodynamics": {
            "onset": "2-3 hours",
            "peak": "2-3 hours",
            "duration": "12-24 hours"
        },
        "adverse_effects": [
            "GI upset (nausea, diarrhea) - most common",
            "Lactic acidosis - rare but serious, risk increased in renal impairment",
            "B12 deficiency with long-term use",
            "Metallic taste"
        ],
        "drug_interactions_mechanism": {
            "ace_inhibitors": "May enhance hypoglycemic effect through improved insulin sensitivity",
            "loop_diuretics": "May increase metformin levels by decreasing renal function",
            "alcohol": "Increases risk of lactic acidosis",
            "iodinated_contrast": "Hold 48 hours before/after contrast due to AKI risk"
        }
    },
    "lisinopril": {
        "mechanism": "ACE inhibitor that blocks conversion of angiotensin I to angiotensin II, reducing vasoconstriction, aldosterone secretion, and bradykinin breakdown. Increases bradykinin levels (causes cough).",
        "pharmacokinetics": {
            "absorption": "Well absorbed orally, bioavailability ~25%",
            "distribution": "Not bound to plasma proteins",
            "metabolism": "Not metabolized",
            "elimination": "Renally cleared unchanged, half-life ~12 hours",
            "clearance": "Dose adjustment needed in renal impairment"
        },
        "pharmacodynamics": {
            "onset": "1 hour",
            "peak": "6-8 hours",
            "duration": "24 hours"
        },
        "adverse_effects": [
            "Dry cough (bradykinin-mediated) - 5-20%",
            "Hyperkalemia",
            "Angioedema - rare but serious",
            "Hypotension, especially on initiation",
            "Acute kidney injury in volume depletion or bilateral renal artery stenosis"
        ],
        "drug_interactions_mechanism": {
            "nsaids": "May reduce antihypertensive effect and worsen renal function via prostaglandin inhibition",
            "potassium_sparing_diuretics": "Additive hyperkalemia risk",
            "lithium": "May increase lithium levels by reducing renal clearance"
        }
    },
    "ibuprofen": {
        "mechanism": "Non-selective COX inhibitor (COX-1 and COX-2), reducing prostaglandin synthesis. COX-1 inhibition causes GI side effects; COX-2 inhibition provides anti-inflammatory effect.",
        "pharmacokinetics": {
            "absorption": "Well absorbed orally",
            "distribution": "Highly protein bound (>99%)",
            "metabolism": "Hepatic metabolism via CYP2C9",
            "elimination": "Renal excretion, half-life ~2 hours",
            "clearance": "Renal and hepatic clearance"
        },
        "pharmacodynamics": {
            "onset": "30-60 minutes",
            "peak": "1-2 hours",
            "duration": "4-6 hours"
        },
        "adverse_effects": [
            "GI ulceration and bleeding",
            "Acute kidney injury, especially in volume depletion",
            "Fluid retention and worsening heart failure",
            "Hypertension",
            "Increased cardiovascular risk with chronic use"
        ],
        "drug_interactions_mechanism": {
            "ace_inhibitors": "Prostaglandin inhibition reduces renal blood flow, worsening renal function and reducing antihypertensive effect",
            "warfarin": "Displaces warfarin from protein binding, increasing free warfarin and bleeding risk",
            "aspirin": "Competes for COX-1 binding site, may reduce cardioprotective effect of low-dose aspirin"
        }
    },
    "warfarin": {
        "mechanism": "Vitamin K antagonist that inhibits vitamin K epoxide reductase, preventing reduction of vitamin K epoxide to vitamin K. This blocks synthesis of vitamin K-dependent clotting factors (II, VII, IX, X).",
        "pharmacokinetics": {
            "absorption": "Well absorbed orally",
            "distribution": "Highly protein bound (>99%), small volume of distribution",
            "metabolism": "Hepatic metabolism via CYP2C9, CYP1A2, CYP3A4",
            "elimination": "Renal excretion of metabolites, half-life ~40 hours",
            "clearance": "Hepatic clearance, many drug interactions"
        },
        "pharmacodynamics": {
            "onset": "24-72 hours (delayed due to existing clotting factors)",
            "peak": "36-72 hours",
            "duration": "2-5 days after discontinuation"
        },
        "adverse_effects": [
            "Bleeding - major risk",
            "Skin necrosis - rare",
            "Purple toe syndrome - rare",
            "Teratogenicity in pregnancy"
        ],
        "drug_interactions_mechanism": {
            "many_antibiotics": "May increase INR by killing gut flora that produce vitamin K",
            "aspirin": "Additive antiplatelet effect increases bleeding risk",
            "nsaids": "GI bleeding risk, may displace warfarin from protein binding"
        }
    },
    "furosemide": {
        "mechanism": "Loop diuretic that inhibits Na-K-2Cl cotransporter in thick ascending limb of loop of Henle, preventing sodium reabsorption and causing diuresis.",
        "pharmacokinetics": {
            "absorption": "Variable oral absorption (~60%)",
            "distribution": "Highly protein bound (>95%)",
            "metabolism": "Minimal hepatic metabolism",
            "elimination": "Renal excretion, half-life ~2 hours",
            "clearance": "Renal clearance"
        },
        "pharmacodynamics": {
            "onset": "30-60 minutes (oral), 5 minutes (IV)",
            "peak": "1-2 hours",
            "duration": "6-8 hours"
        },
        "adverse_effects": [
            "Hypokalemia",
            "Hyponatremia",
            "Hypomagnesemia",
            "Ototoxicity (especially with IV high doses)",
            "Volume depletion and hypotension",
            "Hyperuricemia"
        ],
        "drug_interactions_mechanism": {
            "ace_inhibitors": "Volume depletion may cause excessive hypotension and worsen renal function",
            "digoxin": "Hypokalemia increases digoxin toxicity by reducing Na-K-ATPase activity",
            "aminoglycosides": "Additive ototoxicity risk"
        }
    },
    "digoxin": {
        "mechanism": "Cardiac glycoside that inhibits Na-K-ATPase pump, increasing intracellular sodium. This reduces Na-Ca exchanger activity, increasing intracellular calcium and enhancing cardiac contractility. Also increases vagal tone (slows AV conduction).",
        "pharmacokinetics": {
            "absorption": "Variable oral absorption (~70%)",
            "distribution": "Large volume of distribution, tissue binding",
            "metabolism": "Minimal metabolism",
            "elimination": "Renal excretion (60-80%), half-life ~36 hours",
            "clearance": "Renal clearance, accumulates in renal impairment"
        },
        "pharmacodynamics": {
            "onset": "1-2 hours",
            "peak": "4-6 hours",
            "duration": "3-4 days"
        },
        "adverse_effects": [
            "Nausea, vomiting",
            "Visual changes (yellow-green halos)",
            "Cardiac arrhythmias (especially with toxicity)",
            "Fatigue, weakness"
        ],
        "drug_interactions_mechanism": {
            "loop_diuretics": "Hypokalemia reduces Na-K-ATPase activity, increasing digoxin binding and toxicity",
            "amiodarone": "Increases digoxin levels by reducing renal clearance",
            "verapamil": "Increases digoxin levels"
        }
    }
}


class PharmacologyTool(BaseTool):
    """Tool for retrieving pharmacology information."""
    
    def __init__(self):
        super().__init__("Pharmacology")
        
    async def _run(self, drug_name: str) -> Optional[Dict]:
        """
        Get comprehensive pharmacology information for a drug.
        """
        # Simulate network delay
        await asyncio.sleep(random.uniform(0.2, 0.5))
        
        drug_lower = drug_name.lower()
        
        # Check direct match
        if drug_lower in PHARMACOLOGY_KB:
            return PHARMACOLOGY_KB[drug_lower]
        
        # Check partial matches
        for key, value in PHARMACOLOGY_KB.items():
            if key in drug_lower or drug_lower in key:
                return value
        
        return None

# Singleton instance
_pharmacology_tool = PharmacologyTool()


async def get_drug_pharmacology(drug_name: str) -> Optional[Dict]:
    """Wrapper for backward compatibility and easy import."""
    return await _pharmacology_tool.execute(drug_name)


async def get_drug_mechanism(drug_name: str) -> Optional[str]:
    """Get mechanism of action for a drug."""
    pharmacology = await get_drug_pharmacology(drug_name)
    if pharmacology:
        return pharmacology.get("mechanism")
    return None


async def get_pharmacokinetic_info(drug_name: str) -> Optional[Dict]:
    """Get pharmacokinetic information for a drug."""
    pharmacology = await get_drug_pharmacology(drug_name)
    if pharmacology:
        return pharmacology.get("pharmacokinetics")
    return None


async def get_pharmacodynamic_info(drug_name: str) -> Optional[Dict]:
    """Get pharmacodynamic information for a drug."""
    pharmacology = await get_drug_pharmacology(drug_name)
    if pharmacology:
        return pharmacology.get("pharmacodynamics")
    return None


async def check_pharmacological_interaction(drug1: str, drug2: str) -> Optional[Dict]:
    """Check for pharmacological interaction between two drugs based on mechanisms."""
    pharm1 = await get_drug_pharmacology(drug1)
    pharm2 = await get_drug_pharmacology(drug2)
    
    if not pharm1 or not pharm2:
        return None
    
    # Check if drug1's interactions include drug2
    interactions1 = pharm1.get("drug_interactions_mechanism", {})
    for interaction_drug, mechanism in interactions1.items():
        if interaction_drug in drug2.lower() or drug2.lower() in interaction_drug:
            return {
                "mechanism": mechanism,
                "risk_level": "moderate_to_high",
                "drug1": drug1,
                "drug2": drug2
            }
    
    # Check if drug2's interactions include drug1
    interactions2 = pharm2.get("drug_interactions_mechanism", {})
    for interaction_drug, mechanism in interactions2.items():
        if interaction_drug in drug1.lower() or drug1.lower() in interaction_drug:
            return {
                "mechanism": mechanism,
                "risk_level": "moderate_to_high",
                "drug1": drug1,
                "drug2": drug2
            }
    
    return None


async def get_adverse_effects(drug_name: str) -> List[str]:
    """Get list of adverse effects for a drug."""
    pharmacology = await get_drug_pharmacology(drug_name)
    if pharmacology:
        return pharmacology.get("adverse_effects", [])
    return []


async def check_clearance_pathway(drug_name: str) -> Optional[str]:
    """Check primary clearance pathway for a drug (renal vs hepatic)."""
    pk_info = await get_pharmacokinetic_info(drug_name)
    if pk_info:
        elimination = pk_info.get("elimination", "").lower()
        clearance = pk_info.get("clearance", "").lower()
        
        if "renal" in elimination or "renal" in clearance:
            return "renal"
        elif "hepatic" in elimination or "hepatic" in clearance or "metabolism" in clearance:
            return "hepatic"
    
    return None
