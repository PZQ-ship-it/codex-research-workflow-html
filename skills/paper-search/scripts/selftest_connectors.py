"""Offline failure-recovery, pagination and provenance regressions."""
import contextlib
import io
import json
import os
import unittest
from unittest.mock import patch

import requests
import search_papers_by_open_alex as oa
import search_papers_by_dblp as dblp
import search_papers_by_openreview as orev


def response(data=None, status=200, content_type='application/json', text=None):
    r=requests.Response()
    r.status_code=status
    r.headers['Content-Type']=content_type
    r._content=(text if text is not None else json.dumps(data)).encode()
    r._content_consumed=True
    r.url='https://example.invalid/public-api'
    return r


def binding(**values):
    return {k:{'value':str(v)} for k,v in values.items()}


class OpenAlexTests(unittest.TestCase):
    def test_transient_failure_uses_keyword_with_provenance(self):
        seen=[]
        def call(*args,**kwargs):
            seen.append(kwargs['params'])
            return response(status=503) if len(seen)==1 else response({'results':[{'title':'Paper','primary_location':None}],'meta':{'count':1}})
        with patch.dict(os.environ,{'PAPER_SEARCH_OPENALEX_MODE':'auto'}), patch.object(oa,'request',side_effect=call), contextlib.redirect_stderr(io.StringIO()) as log:
            papers=oa.search_papers_by_open_alex('video',2023,2026,3)
        self.assertIn('search.semantic',seen[0])
        self.assertEqual(seen[1]['search'],'video')
        self.assertEqual(papers[0]['retrieval_method'],'openalex_keyword')
        self.assertIn('semantics differ',log.getvalue())

    def test_auth_and_rate_errors_do_not_switch_backend(self):
        for status in (401,403,429):
            with self.subTest(status=status), patch.dict(os.environ,{'PAPER_SEARCH_OPENALEX_MODE':'auto'}), patch.object(oa,'request',return_value=response(status=status)) as call:
                with self.assertRaises(requests.HTTPError): oa.search_papers_by_open_alex('q',2023,2026,3)
                self.assertEqual(call.call_count,1)

    def test_keyword_pagination_keeps_last_page(self):
        def call(*args,**kwargs):
            page=kwargs['params']['page']
            n=200 if page==1 else 5
            return response({'results':[{'title':f'{page}/{i}'} for i in range(n)],'meta':{'count':205}})
        with patch.dict(os.environ,{'PAPER_SEARCH_OPENALEX_MODE':'keyword'}), patch.object(oa,'request',side_effect=call), patch.object(oa.time,'sleep'):
            self.assertEqual(len(oa.search_papers_by_open_alex('q',2023,2026,205)),205)

    def test_explicit_semantic_does_not_fallback(self):
        with patch.dict(os.environ,{'PAPER_SEARCH_OPENALEX_MODE':'semantic'}), patch.object(oa,'request',return_value=response(status=503)) as call:
            with self.assertRaises(requests.HTTPError): oa.search_papers_by_open_alex('q',2023,2026,3)
            self.assertEqual(call.call_count,1)


class DBLPTests(unittest.TestCase):
    def test_challenge_uses_public_sparql_and_keeps_author_order(self):
        rows=[binding(pub='https://dblp.org/rec/a',title='Video prediction',year=2024,author='Second',ordinal=2),binding(pub='https://dblp.org/rec/a',title='Video prediction',year=2024,author='First',ordinal=1)]
        replies=[response(status=202,content_type='text/html',text='Making sure you are not a bot! Anubis'),response({'results':{'bindings':rows}})]
        with patch.dict(os.environ,{'PAPER_SEARCH_DBLP_BACKEND':'auto'}), patch.object(dblp,'request',side_effect=replies) as call, patch.object(dblp,'_fetch_abstract_from_doi',return_value=''), patch.object(dblp.time,'sleep'), contextlib.redirect_stderr(io.StringIO()) as log:
            papers=dblp.search_papers_by_dblp('video prediction',2023,2026,3)
        self.assertEqual(call.call_args_list[1].args[2],'https://sparql.dblp.org/sparql')
        query=call.call_args_list[1].kwargs['params']['query']
        self.assertIn('STR(?year) >= "2023"',query)
        self.assertEqual(papers[0]['authors'],['First','Second'])
        self.assertEqual(papers[0]['retrieval_method'],'dblp_sparql_title_tokens')
        self.assertIn('Anubis',log.getvalue())

    def test_rest_mode_surfaces_challenge_without_bypass(self):
        with patch.dict(os.environ,{'PAPER_SEARCH_DBLP_BACKEND':'rest'}), patch.object(dblp,'request',return_value=response(status=202,content_type='text/html',text='Anubis')) as call:
            with self.assertRaises(dblp.DBLPResponseError): dblp.search_papers_by_dblp('q',2023,2026,3)
            self.assertEqual(call.call_count,1)

    def test_sparql_does_not_silently_change_advanced_query(self):
        with patch.dict(os.environ,{'PAPER_SEARCH_DBLP_BACKEND':'sparql'}), patch.object(dblp,'request') as call:
            with self.assertRaises(ValueError): dblp.search_papers_by_dblp('author:Smith OR video',2023,2026,3)
            call.assert_not_called()

    def test_rate_limit_is_not_evaded(self):
        with patch.dict(os.environ,{'PAPER_SEARCH_DBLP_BACKEND':'auto'}), patch.object(dblp,'request',return_value=response(status=429)) as call:
            with self.assertRaises(requests.HTTPError): dblp.search_papers_by_dblp('q',2023,2026,3)
            self.assertEqual(call.call_count,1)


class OpenReviewTests(unittest.TestCase):
    venue='ICLR.cc/2026/Conference'
    def note(self,title='stochastic video prediction',venue=None):
        return {'id':'public-id','cdate':1758205494123,'content':{'title':{'value':title},'abstract':{'value':'abstract'},'venueid':{'value':venue or self.venue}}}

    def test_public_search_ignores_configured_credentials_and_preserves_year(self):
        with patch.dict(os.environ,{'PAPER_SEARCH_OPENREVIEW_AUTH':'public','OPENREVIEW_USER':'fake','OPENREVIEW_PASS':'fake'}), patch.object(orev,'_openreview_clients') as login, patch.object(orev,'request',return_value=response({'notes':[self.note()],'count':1})), contextlib.redirect_stderr(io.StringIO()):
            papers=orev.search_papers_by_openreview('stochastic video prediction',2026,2026,1,[self.venue])
        login.assert_not_called()
        self.assertEqual(papers[0]['year'],2026)
        self.assertEqual(papers[0]['publication_date'],'')
        self.assertTrue(papers[0]['submission_date'].startswith('2025'))
        self.assertEqual(papers[0]['retrieval_method'],'openreview_public_search')

    def test_search_scans_past_first_irrelevant_page(self):
        replies=[response({'notes':[self.note('other topic') for _ in range(200)],'count':201}),response({'notes':[self.note()],'count':201})]
        with patch.dict(os.environ,{'PAPER_SEARCH_OPENREVIEW_AUTH':'public'}), patch.object(orev,'request',side_effect=replies) as call, contextlib.redirect_stderr(io.StringIO()):
            papers=orev.search_papers_by_openreview('stochastic video prediction',2026,2026,1,[self.venue])
        self.assertEqual(len(papers),1)
        self.assertEqual(call.call_args_list[1].kwargs['json']['offset'],200)

    def test_rejected_paper_is_not_labeled_as_accepted_venue(self):
        with patch.object(orev,'request',return_value=response({'notes':[self.note(venue=self.venue+'/Rejected_Submission')],'count':1})):
            self.assertEqual(list(orev._public_venue_notes(None,'q',self.venue)),[])

    def test_all_venue_failures_are_not_silent_zero_hits(self):
        class Failed:
            def get_all_notes(self,**kwargs): raise RuntimeError('offline')
        with self.assertRaises(RuntimeError): orev._fetch_venue_notes(Failed(),Failed(),self.venue)

    def test_search_index_cap_reports_partial_coverage(self):
        batch=[self.note() for _ in range(200)]
        with patch.object(orev,'request',return_value=response({'notes':batch,'count':10000})), contextlib.redirect_stderr(io.StringIO()) as log:
            self.assertEqual(len(list(orev._public_venue_notes(None,'q',self.venue))),10000)
        self.assertIn('coverage is partial',log.getvalue())


if __name__=='__main__': unittest.main(verbosity=2)
