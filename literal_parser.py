import re

class LiteralParser:
    def __init__(self, s, i=0): self.s=s; self.i=i; self.refs={}
    def ws(self):
        while self.i<len(self.s) and self.s[self.i].isspace(): self.i+=1
    def string(self):
        quote=self.s[self.i];self.i+=1;out=[]
        escapes={'n':'\n','r':'\r','t':'\t','b':'\b','f':'\f','v':'\v','0':'\0'}
        while self.i<len(self.s):
            c=self.s[self.i];self.i+=1
            if c==quote:return ''.join(out)
            if c=='\\':
                c=self.s[self.i];self.i+=1
                if c in ['u','x']:
                    n=4 if c=='u' else 2;out.append(chr(int(self.s[self.i:self.i+n],16)));self.i+=n
                else:out.append(escapes.get(c,c))
            else:out.append(c)
        raise ValueError('Unterminated string')
    def val(self):
        self.ws();s=self.s;i=self.i
        m=re.match(r'\$R\[(\d+)\]',s[i:])
        if m:
            key=int(m[1]);self.i+=m.end();self.ws()
            if self.s[self.i:self.i+1]=='=':
                self.i+=1;v=self.val();self.refs[key]=v;return v
            return self.refs.get(key,{'__ref__':key})
        c=s[i]
        if c in ['"',"'"]:return self.string()
        if c=='{':
            self.i+=1;out={};self.ws()
            while self.s[self.i]!='}':
                self.ws()
                if self.s[self.i] in ['"',"'"]:k=self.string()
                else:
                    m=re.match(r'(?:-?\d+(?:\.\d+)?|[\w$]+)',self.s[self.i:]);assert m, self.s[self.i:self.i+80]
                    k=m[0];self.i+=m.end()
                self.ws();assert self.s[self.i]==':',self.s[self.i:self.i+80];self.i+=1
                out[k]=self.val();self.ws()
                if self.s[self.i]==',':self.i+=1;self.ws()
                else:break
            assert self.s[self.i]=='}',self.s[self.i:self.i+80];self.i+=1;return out
        if c=='[':
            self.i+=1;out=[];self.ws()
            while self.s[self.i]!=']':
                out.append(self.val());self.ws()
                if self.s[self.i]==',':self.i+=1;self.ws()
                else:break
            assert self.s[self.i]==']',self.s[self.i:self.i+80];self.i+=1;return out
        for a,b in [('!0',True),('!1',False),('true',True),('false',False),('null',None),('void 0',None),('undefined',None)]:
            if s.startswith(a,i):self.i+=len(a);return b
        m=re.match(r'-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?',s[i:])
        if m:self.i+=m.end();return float(m[0]) if any(x in m[0] for x in '.eE') else int(m[0])
        raise ValueError('Unsupported data token '+s[i:i+100])

def extract(s,key):
    # Only parse a constrained literal grammar, never eval page scripts.
    token=re.escape(key)
    matches=list(re.finditer(r'(?<![\w$])(?:'+token+r'|"'+token+r'"|\x27'+token+r'\x27)\s*:',s))
    last=None
    for m in matches:
        try:return LiteralParser(s,m.end()).val()
        except (ValueError,AssertionError,IndexError) as e:last=e
    if last:raise last
    return None
