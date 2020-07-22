
import ddh1 as ddh
import ddh1.taxonomy as taxonomy

import requests
import copy
import datetime
import time
import json
import os
import yaml
import re
import copy

# NB: disussion of new API format is here: http://jira.worldbank.org/jira/browse/DDH2-170

def search(fields=[], filter={}, obj_type='dataset'):
    '''Query the search API

    Parameters:
        fields: an array of fields to return (in addition to 'title')

        filter: a dict of field names and values. If the first (unnamed) argument
                is a dict then it is assumed to be a filter

        obj_type: type of object to search: 'dataset' or 'resource'

    Returns:
      a generator object for iterating over search results

    Examples:
      for nid,dataset in ddh.dataset.search({'field_wbddh_data_type': 'Time Series'}):
        print dataset['title']

      for nid,dataset in ddh.dataset.search(['created'], {'field_wbddh_data_type': 'geospatial'}):
        print nid, dataset['title'], dataset['created']
    '''

    # if 1st argument is a dict then it's the filter, not fields
    if type(fields) is dict:
        filter = fields
        fields = []

    query = copy.copy(filter) # shallow copy should suffice
    taxonomy.update(query, filter)
    query['type'] = obj_type
    for k,v in query.items():
        if v == None:
            raise ddh.TaxonomyError(k, filter[k])

    query = {'filter['+k+']':v for k,v in iter(query.items())}

    _fields = set(fields)
    _fields.update(['title'])

    # NB: nid must be the first element always
    query['fields'] = '[nid,' + ','.join(_fields) + ',]'

    totalRecords = None
    recordsRead  = 0
    query['limit'] = str(250)

    while totalRecords is None or recordsRead < totalRecords:
        query['offset'] = str(recordsRead)
    
        # crude urlencode so as not to escape the brackets
        query_string = '&'.join([k + '=' + str(v) for k,v in query.items()])

        url = '{}://{}/search-service/search_api/datasets?{}'.format(ddh.protocol, ddh.host, query_string)
        ddh.debug_report('Search - {}'.format(url))

        response = get(url)
        totalRecords = response['count']
        if type(response['result']) is dict:
            recordsRead += len(response['result'])
            for k,v in response['result'].items():
                yield k,v


def get(url, obj_type='node'):

    url = str(url)
    if re.match(r'^\d+$', url):
        url = '{}://{}/api/dataset/{}/{}'.format(ddh.protocol, ddh.host, obj_type, url)

    response = requests.get(url, cookies={ddh.session_key: ddh.session_value})
    try:
        result = response.json()
        if type(result) is not dict:
            return None

        return result

    except:
        raise ddh.APIError('get', url, response.text)

    
def ds_template():

    template = {
      'title': None,
      'body': None,
      'type': 'dataset',
      'status': '1',
      'moderation_next_state': 'published',
      'field_wbddh_data_type': None,
      'field_license_wbddh': None,
      'field_exception_s_': None,
      'field_wbddh_dsttl_upi': None,
      'field_wbddh_responsible': 'No',
      'resources': [],
    }

    # NB: 'frequency' is actually periodicity
    tax_fields = ['wbddh_data_class', 'frequency', 'topic', 'granularity_list',
      'wbddh_country', 'wbddh_economy_coverage', 'wbddh_languages_supported']

    for elem in tax_fields:
        template['field_'+elem] = taxonomy.get('field_'+elem, None, default=True)

    return template

def rs_template():
    template = {
        'title': None,
        'type': 'resource',
        'status': '1',
        'moderation_next_state': 'published',
    }

    tax_fields = ['wbddh_resource_type', 'wbddh_data_class']
    for elem in tax_fields:
        template['field_'+elem] = taxonomy.get('field_'+elem, None, default=True)

    return template

def _set_values(d, elem):

    for k,v in elem.items():
        if v is None:
            continue

        if k in ['_field_tags']:
            # freetagging fields have a different format than other taxonomy fields
            if type(v) is list:
                tags = v
            else:
                tags = [v]

            d[k] = {'und': { 'value_field': ' '.join(['"" {} ""'.format(i) for i in tags]) }}
                
        elif k != 'moderation_next_state' and (k == 'field_tags' or taxonomy.is_tax(k)):
            if type(v) is not list:
                v = [v]
            d[k] = {'und': [{'tid': x} for x in v]}
        elif k in ['body', 'field_wbddh_copyright', 'field_wbddh_type_of_license', 'field_wbddh_source', 'field_wbddh_publisher_name', 'field_wbddh_search_tags', 'field_ddh_external_contact_email', 'field_wbddh_depositor_notes', 'field_ddh_harvest_sys_id', 'field_wbddh_reference_system', 'field_related_links_and_publicat', 'field_external_metadata', 'field_wbddh_responsible']:
            if type(v) is str:
                d[k] = {'und': [{'value': v}]}
            else:
                d[k] = {'und': [v]}
        elif k in ['field_link_api']:
            if type(v) is str:
                d[k] = {'und': [{'url': v}]}
            else:
                d[k] = {'und': [v]}
        elif k in ['field_wbddh_dsttl_upi', 'field_wbddh_collaborator_upi']:
            if type(v) is not list:
                v = [v]

            d[k] = {'und': [{'target_id': x} for x in v]}
        elif k in ['og_group_ref']:
            d[k] = {'und': [{'target_id': v, 'field_mode': 'collections'}]}
        elif k in ['field_wbddh_release_date', 'field_wbddh_modified_date', 'field_wbddh_start_date', 'field_wbddh_end_date']:
            d[k] = {'und': [{
                'value': v.strftime('%Y-%m-%d %H:%M:%S'),
                'timezone': 'America/New_York',
                'timezone_db': 'America/New_York',
                'date_type': 'datetime',
            }]}
        elif k in ['field_wbddh_start_date', 'field_wbddh_end_date']:
            d[k] = {'und': [{ 'value': {
              'day': 1,
              'month': 1,
              'year': 2001
            }}]}
            d[k] = {'und': [{ 'value': v.strftime('%Y-%m-%d %H:%M:%S') }]}
            d[k] = {'und': [{ 'value': str(int(time.mktime(v.timetuple()))) }]}
            d[k] = {'und': [{ 'value': 20010101 }]}
        elif k in ['field_wbddh_time_periods']:
            # note: this currently supports only 1 value in the field, but this could be easily improved
            d[k] = {'und': [{ 'value': v.strftime('%Y-%m-%d %H:%M:%S'), 'value2': v.strftime('%Y-%m-%d %H:%M:%S') }]}
            d[k]['und'][0]['show_todate'] = 0
        else:
            d[k] = v


def new_object(ds):

    obj = {}
    _set_values(obj, ds)
    return obj

def update_dataset(nid, ds):
    '''Updates an existing dataset
       
       Parameters:
         nid: the node ID of a dataset

         ds: a (partial) dataset object

       Returns:
         the node ID of the modified dataset, if successful
    '''

    obj = new_object(ds)

    # workflow status defaults to published if undefined 
    if not 'moderation_next_state' in obj:
        obj['moderation_next_state'] = 'published'

    url = '{}://{}/api/dataset/node/{}'.format(ddh.protocol, ddh.host, nid)
    debug_report('Update dataset - {}'.format(url), obj)
    response = requests.put(url, cookies={ddh.session_key: ddh.session_value}, headers={'X-CSRF-Token': ddh.token}, json=obj)
    try:
        data = safe_json(response)
        return data['nid']
    except:
        raise APIError('put', nid, response.text)
    

def append_resource(nid, rsrc, weight=None):
    '''Appends a new resource to an existing dataset

       Parameters:
         nid: the node ID of a dataset

         rsrc: a resource object (returned by rs_template and modified)

       Returns:
         the node ID of the new resource, if successful
    '''
    if type(nid) is dict:
        id = nid['id']
        nid = nid['nid']
    else:
        id = nid

    e = copy.deepcopy(rsrc)
    post_info = None
    if e.get('upload'):
        post_info = {'files[1]': open(e['upload'],'rb'), 'field_name': (None,'field_upload'), 'attach': (None,'1')}
        del e['upload']

    obj = new_object(e)
    obj['field_dataset_ref'] = {'und': [{'target_id': nid}]}
    if weight is not None:
        obj['field_resource_weight'] = {'und': [{'value': weight}]}

    url = '{}://{}/api/dataset/node'.format(ddh.protocol, ddh.host)
    debug_report('Resource Create - {}'.format(url), obj)
    response = requests.post(url, cookies={ddh.session_key: ddh.session_value}, headers={'X-CSRF-Token': ddh.token}, json=obj)
    try:
        data = safe_json(response)
        rsrc_nid = data['nid']
    except:
        raise APIError('resource', id, response.text)

    # attach files
    if post_info is not None:
        url = '{}://{}/api/dataset/node/{}/attach_file'.format(ddh.protocol, ddh.host, rsrc_nid)
        response = requests.post(url, cookies={ddh.session_key: ddh.session_value}, headers={'X-CSRF-Token': ddh.token}, files=post_info)
        try:
            data = safe_json(response)
            fid  = data[0]['fid']
        except:
            raise APIError('upload to {}'.format(rsrc_nid), id, response.text)

    return rsrc_nid
    
def new_dataset(ds, id=None):
    '''adds a new dataset and child resources

       Parameters:

         ds: a dataset object (returned by ds_template and modified)

         id: an optional record identifier, included when exceptions are raised

       Returns:
         an object describing the new dataset, if successful

    '''

    if id is None:
        id = ds.get('field_ddh_harvest_sys_id', None)

    new_ds = {'nid': None, 'id': id, 'resources': None}

    # this variable determines how the module tries to attach child resources to the dataset
    # 'concurrent'     - resource references are included with the initial dataset POST (most efficient)
    # 'posthoc'        - resource references are attached to dataset in a subsequent PUT, as one object
    # 'posthoc2'       - like posthoc, but PUT request is repeated multiple times until all resources are attached (kludgy but works)
    # 'posthoc-single' - attached to data in multiple subsequent PUTs, one per resource (least efficient)
    #
    # Currently the API only works in 'posthoc2' mode

    # 'dataset_first'  - datasets are created first. resources are appended by including the field_dataset_ref element
    #                    which appends them to the dataset
    rsrc_approach = 'dataset_first'
    workflow_state = ds.get('moderation_next_state', 'draft')

    # step B-1: create dataset with resources attached
    e = copy.deepcopy(ds)
    del e['resources']
    obj = new_object(e)
    url = '{}://{}/api/dataset/node'.format(ddh.protocol, ddh.host)

    debug_report('Dataset Create - {}'.format(url), obj)
    response = requests.post(url, cookies={ddh.session_key: ddh.session_value}, headers={'X-CSRF-Token': ddh.token}, json=obj)
    try:
        data = safe_json(response)
        new_ds['nid'] = data['nid']
    except:
        raise APIError(e['type'], id, response.text)

    # step B-2: create resources
    resource_references = []
    for elem in ds['resources']:
        rsrc_id = append_resource(new_ds, elem, len(resource_references))
        resource_references.append({'nid': rsrc_id, 'title': elem['title']})

    new_ds['resources'] = resource_references

    # NB: on this branch the remaining code in this function is all legacy and never gets executed
    # step 3: attach resources
    if len(resource_references) > 0 and rsrc_approach == 'posthoc':
        obj = {
          'moderation_next_state': workflow_state,
          'field_resources': {'und': []}
        }
        for elem in resource_references:
            # obj['field_resources']['und'].append({'target_id': u'{} ({})'.format(elem['title'], elem['nid'])})
            obj['field_resources']['und'].append({'target_id': '{}'.format(elem['nid'])})

        url = '{}://{}/api/dataset/node/{}'.format(ddh.protocol, ddh.host, new_ds['nid'])
        debug_report('Resource Attach - {} (multiple)'.format(url), obj)
        response = requests.put(url, cookies={ddh.session_key: ddh.session_value}, headers={'X-CSRF-Token': ddh.token}, json=obj)
        # print json.dumps(obj, indent=4)
        try:
            data = safe_json(response)
            nid =  data['nid']
        except:
            raise APIError('put', id, response.text)

    if len(resource_references) > 0 and rsrc_approach == 'posthoc2':
        obj = {
          'moderation_next_state': workflow_state,
          'field_resources': {'und': []}
        }
        for elem in resource_references:
            obj['field_resources']['und'].append({'target_id': '{} ({})'.format(elem['title'], elem['nid'])})

        url = '{}://{}/api/dataset/node/{}'.format(ddh.protocol, ddh.host, new_ds['nid'])
        debug_report('Resource Attach - {} (multiple2)'.format(url), obj)
        for i in range(len(resource_references)):
            # Unfortunately, errors or anomalies for these calls usually indicate that the resource was successfully
            # attached but that the server subsequently died without returning a valid HTTP response or JSON object
            # so we just continue on
            try:
                response = None
                response = requests.put(url, cookies={ddh.session_key: ddh.session_value}, headers={'X-CSRF-Token': ddh.token}, json=obj)
                data = safe_json(response)
                nid =  data['nid']

            except requests.exceptions.ConnectionError as err:
                print('Warning: ConnectionError encountered attaching resources to {} - proceeding ({})'.format(new_ds['nid'], i))

            except:
                print('Warning: Error encountered attaching resources to {} - proceeding ({})'.format(new_ds['nid'], i))

    elif len(resource_references) > 0 and rsrc_approach == 'posthoc-single':
        url = '{}://{}/api/dataset/node/{}'.format(ddh.protocol, ddh.host, new_ds['nid'])
        for elem in resource_references:
            obj = {
              'moderation_next_state': workflow_state,
              'field_resources': {'und': [{ 'target_id': '{} ({})'.format(elem['title'], elem['nid'])}] }
            }

            debug_report('Resource Attach - {} (single)'.format(url), obj)
            response = requests.put(url, cookies={ddh.session_key: ddh.session_value}, headers={'X-CSRF-Token': ddh.token}, json=obj)
            try:
                data = safe_json(response)
                nid =  data['nid']
            except:
                raise APIError('put', id, response.text)

    return new_ds
 
def delete(node_id):

    url = '{}://{}/api/dataset/node/{}'.format(ddh.protocol, ddh.host, node_id)

    response = requests.delete(url, cookies={ddh.session_key: ddh.session_value}, headers={'X-CSRF-Token': ddh.token}, json={})
    try:
        result = safe_json(response)

        return 'OK' if result[0] == True else result[0]

    except:
        raise APIError('delete', node_id, response.text)


def safe_json(response):
    if not ddh.hack_mode:
        # in regular mode, we assume that server responses are well formed
        return response.json()
    else:
        # in hack mode, we try to remove bogus messages that result from bugs in the server code. These show up
        # as HTML-formatted text added to the end of a JSON response
        return json.loads(re.sub(r'<br />.+', '', response.text, 0, re.S))

