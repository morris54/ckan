import json
import StringIO
import unicodecsv as csv

import pylons

import ckan.plugins as p
import ckan.lib.base as base
import ckan.model as model

from ckan.common import request


def _dump_nested(column, record):
    name, ctype = column
    value = record[name]

    is_nested = (
        ctype == 'json' or
        ctype.startswith('_') or
        ctype.endswith(']')
    )
    if is_nested:
        return json.dumps(value)
    return value


class DatastoreController(base.BaseController):
    def dump(self, resource_id):
        context = {
            'model': model,
            'session': model.Session,
            'user': p.toolkit.c.user
        }

        data_dict = {
            'resource_id': resource_id,
            'limit': request.GET.get('limit', 100000),
            'offset': request.GET.get('offset', 0)
        }

        action = p.toolkit.get_action('datastore_search')
        try:
            result = action(context, data_dict)
        except p.toolkit.ObjectNotFound:
            base.abort(404, p.toolkit._('DataStore resource not found'))

        pylons.response.headers['Content-Type'] = 'text/csv'
        pylons.response.headers['Content-disposition'] = \
            'attachment; filename="{name}.csv"'.format(name=resource_id)
        f = StringIO.StringIO()
        wr = csv.writer(f, encoding='utf-8')

        header = [x['id'] for x in result['fields']]
        wr.writerow(header)

        columns = [
            (x['id'], x['type'])
            for x in result['fields']]

        for record in result['records']:
            wr.writerow([
                _dump_nested(column, record)
                for column in columns])

        return f.getvalue()
