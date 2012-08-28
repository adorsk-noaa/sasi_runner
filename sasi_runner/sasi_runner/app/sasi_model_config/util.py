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
            return SubstratesValidator(config, section)
        else:
            return None

class SectionValidator(object):
    pass

class DefaultSectionValidator(SectionValidator):
    pass

class FileSectionValidator(SectionValidator):
    def __init__(self, config=None, section=None):
        SectionValidator.__init__(self)
        self.config = config
        self.section = section
        self.section_file = getattr(self.config, self.section)

    def validate(self):
        if not os.path.isfile(self.section_file.path):
            raise ValidationError("File '%s' could not be located." %
                                  self.section_file.filename)

    def get_zfile(self):
        if not hasattr(self, 'zfile'):
            self.zfile = zipfile.ZipFile(self.section_file.path, 'r')
        return self.zfile

    def validate_files_exist(self, required_file_paths):
        zfile = self.get_zfile()
        zfile_contents = zfile.namelist()
        for file_path in required_file_paths:
            if file_path not in zfile_contents:
                raise ValidationError("File '%s' was not found in archive "
                                      "'%s'. This file is required."
                                      % (data_file_path, 
                                         self.section_file.filename)
                                     ) 

    def validate_csv_file(self, file_path, required_columns):
        zfile = self.get_zfile()
        csv_reader = csv.DictReader(zfile.open(file_path, 'rU'))
        for column in required_columns:
            if column not in csv_reader.fieldnames:
                raise ValidationError(
                    "Column '%s' was not found in data file" 
                    " '%s', in archive file '%s'. This column is required."
                    % (column, file_path, self.section_file.filename)) 

class SubstratesValidator(FileSectionValidator):
    def validate(self):
        super(SubstratesValidator, self).validate()
        data_file_path = os.path.join('substrates', 'data', 'substrates.csv')
        self.validate_files_exist([data_file_path])
        self.validate_csv_file(data_file_path, ["id"])
