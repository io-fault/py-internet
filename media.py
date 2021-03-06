"""
# Mime Type structures and parsers for content types and media ranges.

# Interfaces here work exclusively with character-strings; wire data must be decoded.

# [ References ]

	# - &<http://tools.ietf.org/html/rfc6838>

# [ Properties ]

# /types/
	# A mapping of type names and file extensions to MIME type strings.
# /filename_extensions/
	# A mapping of filename extensions to type name.
# /iana_registered_types/
	# The IRI of the set of media types registered with IANA.

# [ Functions ]

# /type_from_string/
	# Construct a &Type instance from a MIME type string.

	# Code:
	#!/pl/python
		from fault.internet import media
		mt = media.type_from_string("text/xml")

	# Equivalent to &Type.from_string, but cached.
# /range_from_string/
	# Construct a &Range instance from a Media Range string like an Accept header.

	# Equivalent to &Range.from_string, but cached.
"""
import operator
import functools
import typing
from . import tools

iana_registered_types = 'https://www.iana.org/assignments/media-types/media-types.xml'

types = {
	'data': 'application/octet-stream', # browsers interpret this as a file download
	'fail': 'application/failure+xml',

	'python-pickle': 'application/x-python-object+pickle',
	'python-marshal': 'application/x-python-object+marshal',
	'python-xml': 'application/x-python-object+xml', # fault.xml format
	# 'structures': 'application/x-conceptual+xml',

	'text': 'text/plain',
	'txt': 'text/plain',
	'rtf': 'application/rtf',

	'cache': 'text/cache-manifest',
	'html': 'text/html',
	'htm': 'text/html',
	'css': 'text/css',

	'pdf': 'application/pdf',
	'postscript': 'application/postscript',

	'javascript': 'text/plain;pl=javascript',
	'py': 'text/plain;pl=python',

	# Recommended types for .js files.
	'json': 'application/json',
	'js': 'application/javascript',

	'xml': 'text/xml',
	'sgml': 'text/sgml',

	'rdf': 'application/rdf+xml',
	'rss': 'application/rss+xml',
	'atom': 'application/atom+xml',
	'xslt': 'application/xslt+xml',
	'xsl': 'application/xslt+xml',

	'zip': 'application/zip',
	'gzip': 'application/gzip',
	'gz': 'application/gzip',
	'bzip2': 'application/x-bzip2',
	'tar': 'application/x-tar',
	'xz': 'application/x-xz',
	'rar': 'application/x-rar-compressed',
	'sit': 'application/x-stuffit',
	'z': 'application/x-compress',

	'tgz': 'application/x-tar+gzip',
	'txz': 'application/x-tar+x-xz',
	'torrent': 'application/x-bittorrent',

	# images
	'svg': 'image/svg+xml',
	'png': 'image/png',
	'gif': 'image/gif',
	'tiff': 'image/tiff',
	'tif': 'image/tiff',
	'jpeg': 'image/jpeg',
	'jpg': 'image/jpeg',

	# video
	'mpg': 'video/mpeg',
	'mpeg': 'video/mpeg',
	'mp2': 'video/mpeg',
	'mov': 'video/quicktime',
	'mp4': 'video/mp4',
	'webm': 'video/webm',
	'ogv': 'video/ogg',
	'avi': 'video/avi',

	# audio
	'mp3': 'audio/mpeg',
	'mid': 'audio/midi',
	'wav': 'audio/x-wav',
	'aif': 'audio/x-aiff',
	'aiff': 'audio/x-aiff',

	'ogg': 'audio/ogg',
	'opus': 'audio/ogg',
	'oga': 'audio/ogg',
	'ogx': 'application/ogg',
	'spx': 'audio/ogg',

	# microsoft
	'xls': 'application/vnd.ms-excel',
	'doc': 'application/msword',
	'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
	'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
	'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
	'ppsx': 'application/vnd.openxmlformats-officedocument.presentationml.slideshow',
	'potx': 'application/vnd.openxmlformats-officedocument.presentationml.template',
}

@functools.lru_cache(32)
def file_type(filename):
	"""
	# Identify the MIME type from a filename using common file extensions.

	# Unidentified extensions will likely return application/octets-stream.
	"""
	global types

	parts = filename.rsplit('.', 1)

	if parts[1] not in types:
		return Type.from_string(types['data'])

	return Type.from_string(types[parts[1]])

class Type(tuple):
	"""
	# An IANA Media Type; the Content-Type, Subtype, and options triple describing
	# the type of data.

	# A container interface (`in`) is provided in order to identify if a given
	# type is considered to be within another:

		# - `text/html in */*`
		# - `text/html in text/*`
		# - `text/html;level=1 in text/html`
		# - `text/html not in text/html;level=1`

	# The &from_string classmethod is the common constructor.
	"""
	__slots__ = ()

	def __str__(self):
		return self.__bytes__().decode('ascii', 'surrogateescape')

	def __bytes__(self, format=b'/'.join):
		# WARNING: recoding of fields.
		if self[2]:
			optjoin = b';'
			encoded = tools.encode_parameters(self[2])
			optstr = tools.join_parameter_series(encoded)
		else:
			optjoin = b''
			optstr = b''

		return format(x.encode('utf-8') for x in self[:2]) + optjoin + optstr

	@property
	def cotype(self):
		"""
		# Content Type; usually one of:

			# - `application`
			# - `text`
			# - `image`
			# - `video`
			# - `model`

		# The initial part of a MIME (media) type.
		"""
		return self[0]

	@property
	def subtype(self):
		"""
		# Subtype; the specific form of the &cotype.
		"""
		return self[1]

	@property
	def parameters(self):
		"""
		# Parameters such as charset for encoding designation.
		"""
		return self[2]

	@property
	def pattern(self) -> bool:
		"""
		# Whether the &Type is a pattern and can match multiple types.
		"""
		return '*' in self[:2]

	def push(self, subtype):
		"""
		# Return a new &Type with the given &subtype appended to the instance's &.subtype.
		"""

		cotype, ssubtype, *remainder = self

		return self.__class__((cotype, '+'.join(ssubtype, subtype))+remainder)

	def pop(self):
		"""
		# Return a new &Type with the last '+'-delimited subtype removed. (inverse of push).
		"""

		cotype, ssubtype, *remainder = self
		index = ssubtype.rfind('+')

		if index == -1:
			# nothing to pop
			return self

		return self.__class__((cotype, ssubtype[:index]) + remainder)

	@classmethod
	def from_bytes(Class, string, **parameters):
		"""
		# Split on the ';' and '/' separators and build an instance.

		# Additional parameters or overrides may be given using keywords.
		"""
		start = string.split(b';', 1)
		ct, st = [x.strip() for x in start[0].split(b'/', 1)]

		params = list(tools.decode_parameters(tools.split_parameter_series((start[1:] or (b'',))[0])))
		params.extend(parameters.items())

		os = frozenset(params)
		return Class((ct.decode('ascii', 'surrogateescape'), st.decode('ascii', 'surrogateescape'), os))

	@classmethod
	def from_string(Class, string, **parameters):
		"""
		# Split on the ';' and '/' separators and build an instance.

		# Additional parameters or overrides may be given using keywords.
		"""
		return Class.from_bytes(string.encode('ascii', 'surrogateescape'), **parameters)

	def __contains__(self, mtype):
		if self.cotype in ('*', mtype[0]):
			# content-type match
			if self.subtype in ('*', mtype[1]):
				# sub-type match
				if not self.parameters or (mtype[2] and mtype[2].issubset(self.parameters)):
					# options match
					return True
		return False

class Range(tuple):
	"""
	# Media Range class for supporting Accept headers.

	# Ranges are a mapping of content-types to an ordered sequence of subtype sets.
	# The ordering of the subtype sets indicates the relative quality.

	# Querying the range for a set of types will return the types with the
	# highest precedence for each content type.

	# &None is used to represent any types, (text)`*`.
	"""
	__slots__ = ()

	@staticmethod
	def split(media_range):
		"""
		# Construct triples describing the &media_range.
		"""
		parts = tools.split_parameter_series(media_range,
			normal=tools._normal_mediarange_area
		)
		parts = iter(parts)

		mtype = next(parts)[0]
		params = []
		quality = None
		for x in parts:
			if x[1] is None and b'/' in x[0]:
				# New type in range.
				yield (mtype.split(b'/'), quality, params or None)
				mtype = x[0]
				params = []
				quality = None
				continue
			else:
				# parameters
				if x[0] == b'q':
					quality = x[1]
				else:
					params.append(x)

		# Remainder.
		yield (mtype.split(b'/'), quality, params or None)

	@classmethod
	def from_string(Class, string):
		"""
		# Instantiate the Range from a string.
		"""

		return Class.from_bytes(string.encode('ascii', 'surrogateescape'))

	@classmethod
	def from_bytes(Class, data, skey = operator.itemgetter(0)):
		"""
		# Instantiate the Range from a bytes object; decoded and passed to &from_string.
		"""

		l = []
		for tpair, quality, parameters in Class.split(data):
			cotype, subtype = [x.decode('ascii', 'surrogateescape') for x in tpair]
			percent = int(float(quality or b'1.0') * 100)
			parameters = list(tools.decode_parameters(parameters or ()))

			l.append((percent, Type((cotype, subtype, frozenset(parameters)))))
		l.sort(key=skey, reverse=True)

		return Class(l)

	def quality(self, mimetype):
		"""
		# Search for a single MIME type in the range.
		# Return identified quality of the type.

		# The quality of a particular type is useful in cases where the
		# server wants to give some precedence to another type.
		# Given that the client accepts XML, but it is a lower quality than HTML,
		# the server may want to send XML anyways.
		"""
		r =  self.query(mimetype)
		if r:
			return r[-1] # quality

	def query(self, *available):
		"""
		# Given a sequence of mime types, return the best match
		# according to the qualities recorded in the range.
		"""
		current = None
		position = None
		quality = 0

		for x in available:
			# PERF: nested loop O(len(available)*len(self))
			for q, mt in self:
				if x in mt or mt in x:
					if q > quality:
						current = x
						position = mt
						quality = q
					elif q == quality:
						if mt in position:
							# same quality, but has precedence
							current = x
							position = mt
					else:
						if current is not None and q < quality:
							# the range is ordered by quality
							# everything past this point is lower quality
							break

		if current is None:
			return None

		return (current, position, quality)

any_type = Type(('*', '*', frozenset()))
any_range = Range([(100, any_type)])

# Cached constructors.
type_from_bytes = functools.lru_cache(32)(Type.from_bytes)
type_from_string = functools.lru_cache(32)(Type.from_string)
range_from_string = functools.lru_cache(32)(Range.from_string)
