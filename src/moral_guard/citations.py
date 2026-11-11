"""Academic and institutional citation registry for moral datasets."""

from typing import Dict, Any

CITATION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "hendrycks/ethics_commonsense": {
        "title": "Aligning AI With Shared Human Values",
        "authors": ["Dan Hendrycks", "Collin Burns", "Steven Basart", "Andrew Critch", "Jerry Li", "Dawn Song", "Jacob Steinhardt"],
        "venue": "Proceedings of the International Conference on Learning Representations (ICLR)",
        "year": 2021,
        "dataset_name": "ETHICS Benchmark (Commonsense Morality)",
        "url": "https://arxiv.org/abs/2012.04907",
        "bibtex": "@inproceedings{hendrycks2021ethics, title={Aligning AI With Shared Human Values}, author={Dan Hendrycks and Collin Burns and Steven Basart and Andrew Critch and Jerry Li and Dawn Song and Jacob Steinhardt}, booktitle={ICLR}, year={2021}}"
    },
    "hendrycks/ethics_deontology": {
        "title": "Aligning AI With Shared Human Values",
        "authors": ["Dan Hendrycks", "Collin Burns", "Steven Basart", "Andrew Critch", "Jerry Li", "Dawn Song", "Jacob Steinhardt"],
        "venue": "Proceedings of the International Conference on Learning Representations (ICLR)",
        "year": 2021,
        "dataset_name": "ETHICS Benchmark (Deontology & Duties)",
        "url": "https://arxiv.org/abs/2012.04907",
        "bibtex": "@inproceedings{hendrycks2021ethics, title={Aligning AI With Shared Human Values}, author={Dan Hendrycks and Collin Burns and Steven Basart and Andrew Critch and Jerry Li and Dawn Song and Jacob Steinhardt}, booktitle={ICLR}, year={2021}}"
    },
    "hendrycks/ethics_justice": {
        "title": "Aligning AI With Shared Human Values",
        "authors": ["Dan Hendrycks", "Collin Burns", "Steven Basart", "Andrew Critch", "Jerry Li", "Dawn Song", "Jacob Steinhardt"],
        "venue": "Proceedings of the International Conference on Learning Representations (ICLR)",
        "year": 2021,
        "dataset_name": "ETHICS Benchmark (Justice & Impartiality)",
        "url": "https://arxiv.org/abs/2012.04907",
        "bibtex": "@inproceedings{hendrycks2021ethics, title={Aligning AI With Shared Human Values}, author={Dan Hendrycks and Collin Burns and Steven Basart and Andrew Critch and Jerry Li and Dawn Song and Jacob Steinhardt}, booktitle={ICLR}, year={2021}}"
    },
    "hendrycks/ethics_utilitarianism": {
        "title": "Aligning AI With Shared Human Values",
        "authors": ["Dan Hendrycks", "Collin Burns", "Steven Basart", "Andrew Critch", "Jerry Li", "Dawn Song", "Jacob Steinhardt"],
        "venue": "Proceedings of the International Conference on Learning Representations (ICLR)",
        "year": 2021,
        "dataset_name": "ETHICS Benchmark (Utilitarianism)",
        "url": "https://arxiv.org/abs/2012.04907",
        "bibtex": "@inproceedings{hendrycks2021ethics, title={Aligning AI With Shared Human Values}, author={Dan Hendrycks and Collin Burns and Steven Basart and Andrew Critch and Jerry Li and Dawn Song and Jacob Steinhardt}, booktitle={ICLR}, year={2021}}"
    },
    "hendrycks/ethics_virtue": {
        "title": "Aligning AI With Shared Human Values",
        "authors": ["Dan Hendrycks", "Collin Burns", "Steven Basart", "Andrew Critch", "Jerry Li", "Dawn Song", "Jacob Steinhardt"],
        "venue": "Proceedings of the International Conference on Learning Representations (ICLR)",
        "year": 2021,
        "dataset_name": "ETHICS Benchmark (Virtue Ethics)",
        "url": "https://arxiv.org/abs/2012.04907",
        "bibtex": "@inproceedings{hendrycks2021ethics, title={Aligning AI With Shared Human Values}, author={Dan Hendrycks and Collin Burns and Steven Basart and Andrew Critch and Jerry Li and Dawn Song and Jacob Steinhardt}, booktitle={ICLR}, year={2021}}"
    },
    "demelin/moral_stories": {
        "title": "Moral Stories: Situated Reasoning about Norms, Intent, Actions, and Consequences",
        "authors": ["Denis Emelin", "Ronan Le Bras", "Jena D. Hwang", "Maxwell Forbes", "Yejin Choi"],
        "venue": "Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing (EMNLP)",
        "year": 2021,
        "dataset_name": "Moral Stories Corpus",
        "url": "https://aclanthology.org/2021.emnlp-main.55/",
        "bibtex": "@inproceedings{emelin-etal-2021-moral, title={Moral Stories: Situated Reasoning about Norms, Intent, Actions, and Consequences}, author={Emelin, Denis and Le Bras, Ronan and Hwang, Jena D. and Forbes, Maxwell and Choi, Yejin}, booktitle={EMNLP}, year={2021}}"
    },
    "social_chem_101": {
        "title": "Social Chemistry 101: Learning to Reason about Social and Moral Norms",
        "authors": ["Maxwell Forbes", "Jena D. Hwang", "Vered Shwartz", "Maarten Sap", "Yejin Choi"],
        "venue": "Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP)",
        "year": 2020,
        "dataset_name": "Social Chemistry 101 (Rules-of-Thumb)",
        "url": "https://aclanthology.org/2020.emnlp-main.48/",
        "bibtex": "@inproceedings{forbes-etal-2020-social, title={Social Chemistry 101: Learning to Reason about Social and Moral Norms}, author={Forbes, Maxwell and Hwang, Jena D. and Shwartz, Vered and Sap, Maarten and Choi, Yejin}, booktitle={EMNLP}, year={2020}}"
    },
    "un_udhr_canonical": {
        "title": "Universal Declaration of Human Rights",
        "authors": ["United Nations General Assembly"],
        "venue": "General Assembly Resolution 217 A",
        "year": 1948,
        "dataset_name": "United Nations International Human Rights Directives",
        "url": "https://www.un.org/en/about-us/universal-declaration-of-human-rights",
        "bibtex": "@misc{un1948udhr, author={United Nations}, title={Universal Declaration of Human Rights}, year={1948}, publisher={UN General Assembly}}"
    }
}


def get_citation_for_source(source_id: str) -> Dict[str, Any]:
    """Retrieve full citation metadata by source identifier."""
    if source_id in CITATION_REGISTRY:
        return CITATION_REGISTRY[source_id]
    
    # Prefix fallback
    for key, citation in CITATION_REGISTRY.items():
        if source_id.startswith(key) or key.startswith(source_id):
            return citation
            
    return {
        "title": "Open Normative & Ethical Consensus Corpus",
        "authors": ["Open Source Alignment Contributors"],
        "venue": "Agent Moral Guard Ingestion Pipeline",
        "year": 2024,
        "dataset_name": source_id,
        "url": "https://github.com/mysukriramli/agent-moral-guard",
        "bibtex": f"@misc{{moral_guard_{source_id}, title={{Dataset {source_id}}}, year={{2024}}}}"
    }
