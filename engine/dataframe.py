import re 

class dataframe:

    def create_frame(self,columns,rows,extract_year=False):
        columns = columns 
        rows = rows
        if extract_year==True:
            for r in rows:
                r.append(re.findall(r"\(\d{4}\)",r[1])[0][1:5])
                r[1] = r[1].replace(re.findall(r"\(\d{4}\)",r[1])[0],'').strip()

            columns.append('year')

        d = {}
        for i,c in enumerate(columns): # 0 , movieId
            for r in rows:
                if c not in ['timestamp']:
                    if c in ['movieId','year','userId']:
                        d.setdefault(c,[]).append(int(r[i]))
                    elif c == 'rating':
                        d.setdefault(c,[]).append(float(r[i]))
                    else:
                        d.setdefault(c,[]).append(r[i])

        return d


