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
            "substrates"
        ]

        for section in sections:
            self.validate_section(section)

    def validate_section(self, section):
        validator = self.get_section_validator(self.config, section)
        if not validator:
            validator = DefaultSectionValidator(self.config, section)
        validator.validate()

    def get_section_validator(self, config=None, section=None):
        if section == 'substrates':
            data_file_path = os.path.join('substrates', 'data', 'substrates.csv')
            return CSVSectionFileValidator(
                config=config, 
                section=section, 
                required_files=[data_file_path],
                csv_requirements=[
                    {
                        'file_path': data_file_path,
                        'required_columns': ['id']
                    }
                ]
            )
        else:
            return None

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

        if not hasattr(self.config, self.section):
            raise ValidationError("Config '%s' has no '%s' file."
                                  " This file is required."
                                  % (self.config.title, self.section)
                                 )
        else:
            self.section_file = getattr(self.config, self.section)

    def validate(self):
        if not os.path.isfile(self.section_file.path):
            raise ValidationError("File '%s' could not be located." %
                                  self.section_file.filename)
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
                                      % (data_file_path, 
                                         self.section_file.filename)
                                     ) 


class CSVFileSectionValidator(FileSectionValidator):
    def __init__(self, csv_requirements=[]):
        FileSectionValidator.__init__(self, **kwargs)
        self.csv_requirements = csv_requirements

    def validate(self):
        super(CSVFileSectionValidator, self).validate()

    def validate_csv_requirements(self):
        zfile = self.get_zfile()
        for requirement in csv_requirements:
            file_path = requirement['file_path']
            required_columns = requirement['required_columns']
            csv_reader = csv.DictReader(zfile.open(file_path, 'rU'))
            for column in required_columns:
                if column not in csv_reader.fieldnames:
                    raise ValidationError(
                        "Column '%s' was not found in data file" 
                        " '%s', in archive file '%s'. This column is required."
                        % (column, file_path, self.section_file.filename)) 
