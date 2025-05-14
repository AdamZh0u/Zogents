from pprint import pprint
from pyzolocal.sqls import gets as g

pprint(g.get_attachments()[0])
