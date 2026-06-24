from nomad.config.models.plugins import SchemaPackageEntryPoint


class DatasetSearchEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from nomad_semantic_web_service.schema_packages.schema_package import m_package

        return m_package


schema_package_entry_point = DatasetSearchEntryPoint(
    name='DatasetSearchSchemaPackage',
    description=('ELN schema for ESRF-style public dataset catalogue search requests.'),
)
