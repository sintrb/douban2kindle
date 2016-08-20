# -*- coding: UTF-8 -*
'''
@author: sintrb
GitHub: https://github.com/sintrb/douban2kindle
'''

import requests, sys, os, json, time, re, base64
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

baseheaders = {
	'User-Agent':'api-client/1 com.douban.frodo/4.1.1(71) Android/22 m2note Meizu m2 note  rom:flyme4',
	# 'Authorization': 'Bearer 33661f122211326435324d11d9402e41'
}

baseparams = {
	'udid': 'd46263a69574d73552f51551574241fecb203ffa',
	'device_id': 'd46263a69574d73552f51551574241fecb203ffa',
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

def md5(s):
	import hashlib
	m2 = hashlib.md5()
	m2.update(s)
	return m2.hexdigest()

def render(tmpl, cxt):
	from jinja2 import Template
	t = Template(open(tmpl).read().decode('utf-8'))
	text = t.render(**cxt)
	return text

class BaseGen(object):
	"""生成器"""
	basedir = None
	targetid = None
	colorimg = True	# 启用彩图
	cache = False	# 启用缓存
	replaceimg = None # 替换图片
	def __init__(self, *args, **kwargs):
		for k,v in kwargs.items():
			if hasattr(self, k):
				setattr(self, k, v)
		self._initargs = args
		self._initkwargs = kwargs

	def getcache(self, key):
		keyfile = os.path.join(self.basedir, key)
		if os.path.exists(keyfile):
			return keyfile
		else:
			return None

	def setcache(self, key, content):
		keyfile = os.path.join(self.basedir, key)
		with open(keyfile, 'wb') as f:
			f.write(content)
		return keyfile



	def getapi(self, url, params=None, cache=True):
		'''请求豆瓣API'''
		key = 'api-%s.json'%(md5(url+('' if not params else '&'.join([u'%s=%s'%(k,v) for k,v in params.items()]))))
		keyfile = cache and self.getcache(key)
		if keyfile:
			print 'url', keyfile
			rjson = json.load(open(keyfile))
			return rjson
		else:
			r = apirequest(url,params=params)
			rjson = r.json()
			self.setcache(key, json.dumps(rjson, indent=True, ensure_ascii=True, encoding="utf-8"))
			return rjson


	def getimg(self, url, cache=True):
		'''获取图片'''
		if self.replaceimg:
			url = self.replaceimg
		key = '%s-%s.jpg'%('img' if self.colorimg else 'gry', md5(url))
		keyfile = cache and self.getcache(key)
		if keyfile:
			return keyfile
		else:
			print 'get image ', url
			from PIL import Image
			r = requests.get(url, stream=True, verify=False)
			content = r.content
			keyfile = self.setcache(key, content)
			if self.colorimg:
				im = Image.open(keyfile).convert("RGB")
			else:
				im = Image.open(keyfile).convert("L")
			im.save(keyfile, "jpeg")
			return keyfile


	def wrapimg(self, html):
		for img in set(re.findall('<img[^>]*>', html)):
			ir = re.findall('src=[\'"](\S+)[\'"]', img)
			if ir:
				imgurl = ir[0]
				nimg = img.replace(imgurl, self.getimg(imgurl))
				html = html.replace(img, nimg)
		return html

class NoteGen(BaseGen):
	"""豆瓣日记生成器"""
	def gen(self):
		# print 'x'
		res = self.getapi('https://frodo.douban.com/api/v2/note/%s'%self.targetid)
		if 'content' not in res:
			return None
		cmtres = self.getapi('https://frodo.douban.com/api/v2/note/%s/comments'%self.targetid)
		pdic = {
			p['tag_name']:p
			for p in res.get('photos') or []
		}

		content = res['content']
		for k,v in pdic.items():
			content = content.replace("img id='%s'"%k,"img id='%s' src='%s'"%(k,v['image']['normal']['url']))

		res['content'] = content
		res['comments'] = cmtres['comments']
		res['photos_count'] = len(res['photos'])
		res['desc'] = res['abstract']

		text = render('../note-tmpl.html', res)
		res['keyfile'] = 'content-note%s.html'%self.targetid
		res['htmlfile'] = self.setcache(res['keyfile'], self.wrapimg(text.encode('utf-8')))
		res['typetext'] = u'日记'
		return res

class AlbumGen(BaseGen):
	"""豆瓣相册生成器"""
	def gen(self):
		album = self.getapi('https://frodo.douban.com/api/v2/photo_album/%s'%self.targetid)
		phtres = self.getapi('https://frodo.douban.com/api/v2/photo_album/%s/photos'%self.targetid)
		if 'photos' not in phtres:
			return None
		album['photos'] = phtres.get('photos',[])# phtres['photos']
		album['photos_count'] = len(album['photos'])
		text = render('../album-tmpl.html', album)
		album['keyfile'] = 'content-album%s.html'%self.targetid
		album['htmlfile'] = self.setcache(album['keyfile'], self.wrapimg(text.encode('utf-8')))
		album['typetext'] = u'相册'
		album['more_pic_urls'] = []# [i['image']['small']['url'] for i in album['photos'][0:2]]
		return album

class KindleGen(BaseGen):
	"""Kindle电子书生成器"""
	GenMap = {
		'note':{
			'typetext':u'日记',
			'genner':NoteGen,
		},
		'album':{
			'typetext':u'相册',
			'genner':AlbumGen,
		}

	}
	items = []
	cxt = {}
	def gen(self):
		import datetime
		items = []
		for item in self.items:
			if item['type'] not in self.GenMap:
				print 'unknow type: %s'%item['type']
				continue
			gm = self.GenMap[item['type']]
			genner = gm['genner'](targetid = item['id'], *self._initargs, **self._initkwargs)
			try:
				res = genner.gen()
			except:
				res = None
			if not res:
				continue
			for k,v in item.items():
				res[k] = v
			items.append(res)
		items = [
			{
			# 'layout':0,
			'id':'toc',
			'title':u'首页',
			'keyfile':'toc.html',
			'typetext':None
			}
		] + [i for i in items] +\
		[
			{
			# 'layout':0,
			'id':'end',
			'title':u'@版权申明',
			'keyfile':'end.html'
			}
		]
		date = datetime.datetime.now().strftime('%Y-%m-%d')
		shortdate = datetime.datetime.now().strftime('%m-%d')
		cxt = {
			'title':u'豆瓣%s'%shortdate,
			'date':date,
			'shortdate':shortdate,
			'time':datetime.datetime.now().strftime('%H:%M:%S'),
			'language':'zh',
			'creator':'Douban2Kindle',
			'publisher':'Douban2Kindle',
			'subject':'',
			'description':u'豆瓣%s内容整理'%date,
			'items':items,
		}
		for k,v in self.cxt.items():
			cxt[k] = v
		self.setcache('toc.html', self.wrapimg(render('../toc-tmpl.html', cxt)).encode('utf-8'))
		self.setcache('end.html', self.wrapimg(render('../end-tmpl.html', cxt)).encode('utf-8'))
		self.setcache('kindle.ncx', render('../kindle-tmpl.ncx', cxt).encode('utf-8'))
		return self.setcache('kindle.opf', render('../kindle-tmpl.opf', cxt).encode('utf-8'))


class IDsKindleGen(BaseGen):
	"""Kindle电子书生成器"""
	GenMap = {
		'note':{
			'urlgetter':lambda x: 'https://frodo.douban.com/api/v2/note/%s'%(x['id']),
			'itemgetter':lambda j: {'title':j['title'], 'desc':j['abstract'], 'author':j['author'], 'cover_url':j['cover_url']}
		},
		'album':{
			'urlgetter':lambda x: 'https://frodo.douban.com/api/v2/photo_album/%s'%(x['id']),
			'itemgetter':lambda j: {'title':j['title'], 'desc':j['abstract'], 'author':j['owner'], 'cover_url':j['cover_url']}
		}
	}
	items = []
	def gen(self):
		items = []
		for item in self.items:
			if item['type'] not in self.GenMap:
				print 'unknow type: %s'%item['type']
				continue
			gm = self.GenMap[item['type']]
			url = gm['urlgetter'](item)
			rjson = self.getapi(url)
			nitem = gm['itemgetter'](rjson)
			nitem['type'] = item['type']
			nitem['id'] = item['id']
			items.append(nitem)
			if 'items' in self._initkwargs:
				del self._initkwargs['items']
		kg = KindleGen(items=items, *self._initargs, **self._initkwargs)
		return kg.gen()

class AppGen(BaseGen):
	"""APP首页数据"""
	ReMap = {
		'note':'douban://douban\.com/note/(\d+)',
		'album':'douban://douban\.com/photo_album/(\d+)'
	}
	gens = []
	def getitems(self):
		rjson = self.getapi('https://frodo.douban.com/api/v2/recommend_feed?5', cache=self.cache)
		items = []
		for feed in rjson['recommend_feeds']:
			res = None
			for t,v in self.ReMap.items():
				r = re.findall(v, feed['target']['uri'])
				if r:
					feed['type'] = t
					feed['id'] = r[0]
					feed['desc'] = feed['target']['desc']
					res = feed
					break
			if not res:
				# 页面型, 如 https://m.douban.com/page/jq77s7y
				pass
			if not res:
				# 评论型, 如 douban://douban.com/review/8019965
				pass
			if not res:
				# print 'ignore', feed['target']['uri'], feed
				# res = feed
				# res['keyfile'] = False
				# res['typetext'] = u'未知'
				continue

			if res:
				items.append(res)
		return items

	def gen(self):
		import datetime
		items = self.getitems()
		if not items:
			print 'no'
			return
		date = datetime.datetime.now().strftime('%Y-%m-%d')
		shortdate = datetime.datetime.now().strftime('%m-%d')
		cxt = {
			'title':u'豆瓣APP%s'%shortdate,
		}
		kg = KindleGen(cxt=cxt, items=items, *self._initargs, **self._initkwargs)
		return kg.gen()


class UserNotesGen(BaseGen):
	"""用户日记生成器"""
	userid = None
	def gen(self):
		url = 'https://frodo.douban.com/api/v2/user/%s/notes'%self.userid
		noteids = []
		while True:
			res = self.getapi(url, params={'start':len(noteids)})
			noteids += [n['id'] for n in res['notes']]
			if len(noteids) >= res['total']:
				break
		items = [{'type':'note','id':i} for i in noteids]
		ikg = IDsKindleGen(items=items, *self._initargs, **self._initkwargs)
		return ikg.gen()
		

basedir = os.path.join(os.path.dirname(os.getcwd()), 'kindle2')
try:
	os.makedirs(basedir)
except:
	pass


# notes = []
# targetids = ['570337277','570145876','556174010','536660948','532987130','526627884','418097831','434613956']
# targetids.sort()
# for targetid in targetids:
# 	ng = NoteGen(basedir = basedir, targetid = targetid)
# 	res = ng.gen()
# 	if res:
# 		notes.append(res)


# ag = AppGen(basedir = basedir, colorimg=True, cache=True, gens=['note','album'], replaceimg=None)#'http://7jpthm.com1.z0.glb.clouddn.com/image2.png')
# print ag.gen()


# items = [
# 	{
# 	'type':'note',
# 	'id':'570337277'
# 	},
# 	{
# 	'type':'album',
# 	'id':'1633169751'
# 	}
# ]

# ikg = IDsKindleGen(items=items, basedir = basedir, colorimg=True, cache=True, gens=['note','album'], replaceimg=None)
# ikg.gen()


ung = UserNotesGen(userid='51905389', basedir = basedir, colorimg=True, cache=True, gens=['note','album'], replaceimg=None)
print ung.gen()
# ./kindlegen.exe -locale zh /d/MyDoc/git/douban2kindle/kindle/kindle.opf
