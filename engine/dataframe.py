import re 

class dataframe:

    def create_frame(self, columns, rows, extract_year=False):
        columns = columns
        rows = rows

        if extract_year == True:
            for r in rows:
                if len(r) > 1:
                    yrs = re.findall(r"\(\d{4}\)", r[1])
                    if yrs:
                        year_val = yrs[0][1:5]
                        r.append(year_val)
                        r[1] = r[1].replace(yrs[0], '').strip()
                    else:   
                        r.append('0')
                else:
                    r.append('0')

            columns.append('year')

        d = {}
        for i, c in enumerate(columns):  # 0 , movieId
            for r in rows:
                if c not in ['timestamp']:
                    if c in ['movieId', 'year', 'userId']:
                        d.setdefault(c, []).append(int(r[i]))
                    elif c == 'rating':
                        d.setdefault(c, []).append(float(r[i]))
                    else:
                        d.setdefault(c, []).append(r[i])

        return d
