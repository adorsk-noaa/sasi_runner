import os


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

    def validate(self):
        section_file = getattr(self.config, self.section)
        if not os.path.isfile(section_file.path):
            raise ValidationError("File '%s' could not be located." %
                                  section_file.filename)

class SubstratesValidator(FileSectionValidator):
    pass
