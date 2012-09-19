from flask import request, Markup


def request_wants_json():
    best = request.accept_mimetypes \
            .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
            request.accept_mimetypes[best] > \
            request.accept_mimetypes['text/html']

def format_script_asset(type_='text/javascript', **kwargs):
    asset = '<script '
    for key, value in kwargs.items() + [('type', type_)]:
        asset += '%s="%s" ' % (key, value)
    asset += '></script>'
    return Markup(asset)

def format_link_asset(rel='stylesheet', type_='text/css', **kwargs):
    asset = '<link '
    for key, value in kwargs.items() + [('rel', rel), ('type', type_)]:
        asset += '%s="%s" ' % (key, value)
    asset += '>'
    return Markup(asset)



