def get_synthetic_context():
    return {
        "company": {
            "name": "Northstar RevOps",
            "industry": "B2B SaaS",
            "target_personas": [
                "VP Marketing",
                "Revenue Operations Manager",
                "Sales Director",
            ],
        },
        "campaigns": [
            {
                "name": "Q2 Pipeline Accelerator",
                "channel": "LinkedIn Ads",
                "budget": 12000,
            },
            {
                "name": "AI Ops Webinar Series",
                "channel": "Email + Landing Page",
                "budget": 5000,
            },
        ],
        "sample_leads": [
            {
                "firstname": "Avery",
                "lastname": "Cole",
                "email": "avery.cole@example.com",
                "company": "BrightPath AI",
            },
            {
                "firstname": "Jordan",
                "lastname": "Mills",
                "email": "jordan.mills@example.com",
                "company": "Helio Works",
            },
        ],
    }
