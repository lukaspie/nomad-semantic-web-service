from typing import TYPE_CHECKING

from nomad.config import config
from nomad.datamodel.data import ArchiveSection, Schema, UseCaseElnCategory
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.metainfo import Datetime, MEnum, Quantity, SchemaPackage
from nomad.metainfo.metainfo import Section, SubSection

from nomad_semantic_web_service.catalogue.icat import landing_page_for_dataset
from nomad_semantic_web_service.catalogue.ontology import query_panet_to_esrfet
from nomad_semantic_web_service.catalogue.search import (
    normalize_esrfet_term,
    search_icat_datasets,
    search_local_datasets,
    technique_pids_of,
)

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

configuration = config.get_plugin_entry_point(
    'nomad_semantic_web_service.schema_packages:schema_package_entry_point'
)

m_package = SchemaPackage()


class MatchedDataset(ArchiveSection):
    m_def = Section(label='Matched dataset')

    dataset_id = Quantity(type=int, description='The catalogue-internal dataset id.')
    name = Quantity(type=str, description='Dataset title.')
    start_date = Quantity(type=Datetime, description='Start date-time of the dataset.')
    end_date = Quantity(type=Datetime, description='End date-time of the dataset.')
    instrument_name = Quantity(
        type=str, description='Name of the beamline or instrument.'
    )
    technique_pids = Quantity(
        type=str,
        shape=['*'],
        description='ESRFET technique IRIs associated with the dataset.',
    )
    sample_name = Quantity(type=str, description='Name/description of the sample.')
    landing_page = Quantity(
        type=str,
        description=(
            'DOI-based landing page for the dataset (https://doi.org/<doi>), '
            'resolved from the dataset record. Not a direct file download link: '
            'ICAT+ has no generic, unauthenticated download URL for the '
            'underlying files.'
        ),
    )


class DatasetSearchRequest(Schema):
    """
    A structured search request for ESRF-style public dataset catalogues,
    modeled after the oscarsSemanticWebService CLI's interactive prompts.
    """

    m_def = Section(label='Dataset search request', categories=[UseCaseElnCategory])

    synchrotron = Quantity(
        type=MEnum('ESRF', 'Diamond Light Source', 'MAX IV'),
        default='ESRF',
        description=(
            'Synchrotron to search. Only ESRF is currently wired to a live '
            'catalogue endpoint; the others are placeholders.'
        ),
        a_eln=ELNAnnotation(component=ELNComponentEnum.EnumEditQuantity),
    )
    vocabulary = Quantity(
        type=MEnum('ESRFET', 'PANET'),
        default='ESRFET',
        description=(
            'Vocabulary used for technique_term. ESRFET terms are used directly; '
            'PANET terms are first mapped to an equivalent ESRFET term via the '
            'local ontology before searching.'
        ),
        a_eln=ELNAnnotation(component=ELNComponentEnum.RadioEnumEditQuantity),
    )
    technique_term = Quantity(
        type=str,
        description=(
            'Technique term, IRI, or compact curie. For vocabulary=ESRFET, e.g. '
            '"XAS" or "ESRFET:XAS". For vocabulary=PANET, e.g. "PaNET01196" or '
            '"PaNET:PaNET01196".'
        ),
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )
    start_date = Quantity(
        type=Datetime,
        default='2024-01-01T00:00:00+00:00',
        description='Start date-time of the search window.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.DateTimeEditQuantity),
    )
    end_date = Quantity(
        type=Datetime,
        default='2024-12-31T23:59:59+00:00',
        description='End date-time of the search window.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.DateTimeEditQuantity),
    )
    instrument_name = Quantity(
        type=str,
        description='Optional beamline or instrument name to filter by.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )
    use_real_icat = Quantity(
        type=bool,
        default=False,
        description=(
            'If set, search the real ESRF ICAT+ public datasets endpoint instead '
            'of the local demo data. Requires network access to icatplus.esrf.fr.'
        ),
        a_eln=ELNAnnotation(component=ELNComponentEnum.BoolEditQuantity),
    )

    resolved_technique_term = Quantity(
        type=str,
        description=(
            'The ESRFET IRI actually used for the search, after PANET->ESRFET '
            'mapping if vocabulary=PANET. Review this before running the search.'
        ),
    )
    mapping_warning = Quantity(
        type=str,
        description='Set if a PANET->ESRFET mapping could not be resolved.',
    )
    trigger_search = Quantity(
        type=bool,
        default=False,
        description=(
            'Runs the catalogue search using resolved_technique_term. Kept as an '
            'explicit action, not an automatic step, so a PANET->ESRFET mapping can '
            'be reviewed before it is used to search (mirrors the confirmation '
            'prompt in the original CLI agent).'
        ),
        a_eln=ELNAnnotation(component=ELNComponentEnum.ActionEditQuantity, label='Run Search'),
    )
    matched_datasets = SubSection(section_def=MatchedDataset, repeats=True)

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

        self.mapping_warning = None

        # Quantity defaults are returned as the raw literal (e.g. a str) until
        # explicitly assigned, which is what triggers the Datetime type's
        # coercion to a real datetime. Re-assigning forces that coercion even
        # when start_date/end_date were never set and are still at default.
        self.start_date = self.start_date
        self.end_date = self.end_date

        if self.synchrotron != 'ESRF':
            logger.warning(f'{self.synchrotron} is not wired to a live endpoint yet.')
            self.trigger_search = False
            return
        if not self.technique_term:
            self.trigger_search = False
            return

        if self.vocabulary == 'PANET':
            mappings = query_panet_to_esrfet(self.technique_term)
            if not mappings:
                self.mapping_warning = 'No ESRFET mapping found for this PANET term.'
                self.trigger_search = False
                return
            self.resolved_technique_term = mappings[0]['targetTerm']
        else:
            self.resolved_technique_term = normalize_esrfet_term(self.technique_term)

        if not self.trigger_search:
            return

        try:
            self._run_search(archive, logger)
        finally:
            self.trigger_search = False

    def _run_search(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        from nomad.datamodel.context import ServerContext

        if self.use_real_icat and not isinstance(archive.m_context, ServerContext):
            # Skip the outbound ICAT+ call in offline/test contexts.
            return

        try:
            search = search_icat_datasets if self.use_real_icat else search_local_datasets
            raw = search(
                self.start_date,
                self.end_date,
                self.resolved_technique_term,
                self.instrument_name,
            )
        except Exception:
            logger.error('Catalogue search failed.', exc_info=True)
            return

        if not isinstance(raw, list):
            logger.warning('Catalogue search returned an unexpected response shape.')
            return

        self.matched_datasets = [
            MatchedDataset(
                dataset_id=dataset.get('id'),
                name=dataset.get('name'),
                start_date=dataset.get('startDate'),
                end_date=dataset.get('endDate'),
                instrument_name=dataset.get('instrumentName'),
                technique_pids=technique_pids_of(dataset),
                sample_name=dataset.get('sampleName'),
                landing_page=landing_page_for_dataset(dataset),
            )
            for dataset in raw
            if isinstance(dataset, dict)
        ]


m_package.__init_metainfo__()
