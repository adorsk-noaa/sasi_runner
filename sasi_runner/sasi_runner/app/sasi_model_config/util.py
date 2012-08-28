import os
import zipfile
import csv


def validate_config(config):
    config_validator = ConfigValidator(config=config)
    config_validator.validate()

class ValidationError(Exception): pass

class ConfigValidator(object):

    def __init__(self, config=None):
        self.config = config

    def validate(self):
        """ Validate config, section by section."""
        sections = [
            'substrates',
            'features',
            'gears',
            'va'
        ]

        for section in sections:
            self.validate_section(section)

    def validate_section(self, section):
        validator = self.get_section_validator(self.config, section)
        if validator:
            validator.validate()

    def get_section_validator(self, config=None, section=None):
        validator = None

        if section in [
            'substrates',
            'features',
            'gears',
            'va',
        ] :
            data_file_path = os.path.join(section, 'data', section + '.csv')
            required_file_paths = [data_file_path]

            required_columns = []
            if section == 'substrates':
                required_columns = [
                    'id'
                ]
            elif section == 'features':
                required_columns = [
                    'id', 
                    'category'
                ]
            elif section == 'va':
                required_columns = [
                    "Gear ID", 
                    "Substrate ID",
                    "Feature ID",
                    "Energy",
                    "S",
                    "R"
                ]

            validator = CSVFileSectionValidator(
                config=config, 
                section=section, 
                required_file_paths=required_file_paths,
                csv_requirements=[{
                    'file_path': data_file_path,
                    'required_columns': required_columns
                }]
            )

        return validator

class SectionValidator(object):
    pass

class DefaultSectionValidator(SectionValidator):
    pass

class FileSectionValidator(SectionValidator):
    def __init__(self, config=None, section=None, required_file_paths=[]):
        SectionValidator.__init__(self)
        self.config = config
        self.section = section
        self.required_file_paths = required_file_paths

        if not getattr(self.config, self.section):
            raise ValidationError("Config '%s' has no '%s' file assigned."
                                  " This file is required."
                                  " Names are case-sensitive."
                                  % (self.config.title, self.section)
                                 )
        else:
            self.section_file = getattr(self.config, self.section)

    def validate(self):
        if not getattr(self.section_file, 'path'):
            raise ValidationError("'%s' file has no valid path."
                                 % self.section)
        if not os.path.isfile(self.section_file.path):
            raise ValidationError("File '%s' could not be located."
                                  " Names are case-sensitive." 
                                  % self.section_file.filename)
        self.validate_required_files()

    def get_zfile(self):
        if not hasattr(self, 'zfile'):
            self.zfile = zipfile.ZipFile(self.section_file.path, 'r')
        return self.zfile

    def validate_required_files(self):
        zfile = self.get_zfile()
        zfile_contents = zfile.namelist()
        for file_path in self.required_file_paths:
            if file_path not in zfile_contents:
                raise ValidationError("File '%s' was not found in archive "
                                      "'%s'. This file is required."
                                      " Names are case-sensitive."
                                      % (file_path, 
                                         self.section_file.filename)
                                     ) 


class CSVFileSectionValidator(FileSectionValidator):
    def __init__(self, csv_requirements=[], **kwargs):
        FileSectionValidator.__init__(self, **kwargs)
        self.csv_requirements = csv_requirements

    def validate(self):
        super(CSVFileSectionValidator, self).validate()
        zfile = self.get_zfile()
        for requirement in self.csv_requirements:
            file_path = requirement['file_path']
            required_columns = requirement['required_columns']
            csv_reader = csv.DictReader(zfile.open(file_path, 'rU'))
            for column in required_columns:
                if column not in csv_reader.fieldnames:
                    raise ValidationError(
                        "Column '%s' was not found in data file" 
                        " '%s', in archive file '%s'. This column is required."
                        " Names are case-sensitive."
                        % (column, file_path, self.section_file.filename)) 
