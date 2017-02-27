from cloudify import ctx


def under_to_camel(s):
    flag = False
    first = True
    out = ""
    for c in s:
        if c == '_':
            flag = True
        else:
            out = out + c if not flag and not first else out + c.upper()
            flag = False
        first = False
    ctx.logger.info("converted {} to {}".format(s, out))
    return out


def camelmap(mapin, ignore=[], exclude=[]):
    if isinstance(mapin, type(list())):
        out = []
        for v in mapin:
            out.append(camelmap(v))
    else:
        out = {}
        for k, v in mapin.iteritems():
            if k not in ignore:
                if (isinstance(v, type(dict())) or isinstance(
                        v, type(list()))) and k not in exclude:
                    out[under_to_camel(k)] = camelmap(v)
                else:
                    out[under_to_camel(k)] = v

    return out
