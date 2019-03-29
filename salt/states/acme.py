# -*- coding: utf-8 -*-
'''
ACME / Let's Encrypt certificate management state
=================================================

.. versionadded: 2016.3

See also the module documentation

.. code-block:: yaml

    reload-gitlab:
      cmd.run:
        - name: gitlab-ctl hup

    dev.example.com:
      acme.cert:
        - aliases:
          - gitlab.example.com
        - email: acmemaster@example.com
        - webroot: /opt/gitlab/embedded/service/gitlab-rails/public
        - renew: 14
        - fire_event: acme/dev.example.com
        - onchanges_in:
          - cmd: reload-gitlab

'''
# Import python libs
from __future__ import absolute_import, print_function, unicode_literals
import logging

log = logging.getLogger(__name__)


def __virtual__():
    '''
    Only work when the ACME module agrees
    '''
    return 'acme.cert' in __salt__


def cert(name,
         aliases=None,
         email=None,
         webroot=None,
         test_cert=False,
         renew=None,
         keysize=None,
         server=None,
         owner='root',
         group='root',
         mode='0640',
         certname=None):
    '''
    Obtain/renew a certificate from an ACME CA, probably Let's Encrypt.

    :param name: Common Name of the certificate (DNS name of certificate)
    :param aliases: subjectAltNames (Additional DNS names on certificate)
    :param email: e-mail address for interaction with ACME provider
    :param webroot: True or a full path to webroot. Otherwise use standalone mode
    :param test_cert: Request a certificate from the Happy Hacker Fake CA (mutually exclusive with 'server')
    :param renew: True/'force' to force a renewal, or a window of renewal before expiry in days
    :param keysize: RSA key bits
    :param server: API endpoint to talk to
    :param owner: owner of the private key file
    :param group: group of the private key file
    :param mode: mode of the private key file
    :param certname: Name of the certificate to save
    '''

    if certname is None:
        certname = name

    if __opts__['test']:
        ret = {
            'name': certname,
            'changes': {},
            'result': None
        }
        window = None
        try:
            window = int(renew)
        except Exception:
            pass

        comment = 'Certificate {0} '.format(certname)
        if not __salt__['acme.has'](certname):
            comment += 'would have been obtained'
        elif __salt__['acme.needs_renewal'](certname, window):
            comment += 'would have been renewed'
        else:
            comment += 'would not have been touched'
            ret['result'] = True
        ret['comment'] = comment
        return ret

    if not __salt__['acme.has'](certname):
        old = None
    else:
        old = __salt__['acme.info'](certname)

    res = __salt__['acme.cert'](
        name,
        aliases=aliases,
        email=email,
        webroot=webroot,
        certname=certname,
        test_cert=test_cert,
        renew=renew,
        keysize=keysize,
        server=server,
        owner=owner,
        group=group,
        mode=mode
    )

    ret = {
        'name': certname,
        'result': res['result'] is not False,
        'comment': res['comment']
    }

    if res['result'] is None or res['comment'].endswith('unchanged'):
        ret['changes'] = {}
    else:
        if not __salt__['acme.has'](certname):
            new = None
        else:
            new = __salt__['acme.info'](certname)

        ret['changes'] = {
            'old': old,
            'new': new
        }

    return ret
