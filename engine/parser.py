class csvreader:

    def quote_split(self, s, sep=','):
        s = s.rstrip("\r\n")
        out, buf, q = [], [], False
        i, n = 0, len(s)

        while i < n:
            ch = s[i]
            if ch == '"':
                if q and i + 1 < n and s[i + 1] == '"':
                    buf.append('"')
                    i += 2
                else:
                    q = not q
                    i += 1
            elif ch == sep and not q:
                
                out.append(''.join(buf))
                buf = []
                i += 1
            else:
                buf.append(ch)
                i += 1

        out.append(''.join(buf))
        return out


    def read_doc(self, path, sep=','):

        b = []
        try:
            with open(path, 'r', encoding="utf-8") as a:

                for i in a:
                    
                    if not i.strip():
                        continue

                    if '"' in i:
                        b.append(self.quote_split(i, sep))
                    else:
                        cur = i.strip().split(sep)
                        b.append(cur)

                return b[0], b[1:]
        except FileNotFoundError:
            print("There is no file at the given path, please check")
