from pathlib import Path

import pytest

NGINX_CONF = Path(__file__).resolve().parents[2] / 'nginx' / 'nginx.conf'


@pytest.fixture(scope='module')
def content():
    return NGINX_CONF.read_text()


def test_both_vhosts_serve_new_domain(content):
    assert content.count('server_name tempo-app.site www.tempo-app.site;') == 2


def test_redirect_targets_new_domain(content):
    assert 'return 301 https://tempo-app.site$request_uri;' in content


def test_tls_cert_paths_use_new_domain(content):
    assert 'ssl_certificate /etc/letsencrypt/live/tempo-app.site/fullchain.pem;' in content
    assert 'ssl_certificate_key /etc/letsencrypt/live/tempo-app.site/privkey.pem;' in content


def test_no_old_domain_in_nginx_config(content):
    assert 'tempo-app.xyz' not in content
