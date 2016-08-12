# -*- coding: UTF-8 -*
'''
@author: sintrb
'''
"""
"""

import requests, sys, os, json, time

baseheaders = {
	'User-Agent':'api-client/1 com.douban.frodo/4.1.1(71) Android/22 m2note Meizu m2 note  rom:flyme4',
	# 'Authorization': 'Bearer 33661f122211326435324d11d9402e41'
}

baseparams = {
'udid': 'd46263a69574d73552f51551574241fecb2f3ffa',
'device_id': 'd46263a69572d13551f5655c574241fecb2f3ffa',
'channel': 'Meizu_Market',
'apiKey': '0dad551ec0f84ed02907ff5c42e8ec70',
'os_rom': 'flyme4',
}

def mergedict(d1, d2):
	if not d1 or not d2:
		return d1 or d2 or {}
	d = d2.copy()
	d.update(d1)
	return d

def apirequest(url, params=None, headers=None):
	print '\t',url, '&'.join(['%s=%s'%(k,v) for k,v in params.items()]) if params else None, '&'.join(['%s=%s'%(k,v) for k,v in headers.items()]) if headers else None
	return requests.get(url, params=mergedict(params, baseparams), headers=mergedict(headers, baseheaders), verify=False)

def dataof(d,k,p):
	v = d.get(k)
	if callable(v):
		return v(p)
	else:
		return v

tests = [
	{
	'name':'首页数据',
	'url':'https://frodo.douban.com/api/v2/recommend_feed',
	},
	{
	'name':'首页数据.第二页',
	'url':'https://frodo.douban.com/api/v2/recommend_feed',
	'params':lambda prev: {'since_id':prev and prev['recommend_feeds'][-1]['id']}
	},
	{
	'name':'日记数据',
	'url':'https://frodo.douban.com/api/v2/note/574199886',
	},
	{
	'name':'日记评论',
	'url':'https://frodo.douban.com/api/v2/note/574199886/comments',
	},
	{
	'name':'日记相关推荐',
	'url':'https://frodo.douban.com/api/v2/note/575280360/recommendations',
	},
]

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

prevres = None
for ix, t in enumerate(tests):
	print 'Doing %d: %s...'%(ix, t['name'])
	st = time.time()
	r = apirequest(dataof(t, 'url', prevres), dataof(t, 'params', prevres), dataof(t, 'headers', prevres))
	rjson = r.json()
	with open('res.%s.json'%ix,'wb') as f:
		f.write(json.dumps(rjson, indent=True, ensure_ascii=True, encoding="utf-8"))
	print '\t', time.time()-st
	prevres = rjson

# print open('res.json','wb').write()