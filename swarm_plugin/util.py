from cloudify import ctx, context

def under_to_camel(s):
  flag=False
  first=True
  out=""
  for c in s:
    if c == '_':
      flag=True
    else:
      out = out + c if not flag and not first else out + c.upper()
      flag=False
    first=False
  ctx.logger.info("converted {} to {}".format(s,out))
  return out

def camelmap(mapin,ignore=[],exclude=[]):
  if type(mapin) == type(list()):
    out=[]
    for v in mapin:
      out.append(camelmap(v))
  else:
    out={}
    for k,v in mapin.iteritems():
      if not k in ignore:
        if (type(v) == type(dict()) or type(v) == type(list())) and not k in exclude:
          out[under_to_camel(k)]=camelmap(v)
        else:
          out[under_to_camel(k)]=v

  return out

