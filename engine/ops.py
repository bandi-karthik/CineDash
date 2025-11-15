

class functions:

    def df_len(self,df):
        
        return len(df[list(df.keys())[0]])

    def head(self,df,rows=None):
        d = {}

        for i in df.keys():
            if rows:
                d[i] = df[i][:rows]
            else:
                d[i] = df[i][:5]

        return d 
    
    def tail(self,df,rows=None):
        d = {}
        l = self.df_len(df)
        for i in df.keys():
            if rows:
                d[i] = df[i][l-rows:]
            else:
                d[i] = df[i][l-5:]
        
        return d
    
    def select_columns(self,df,cols):
        d = {}
        
        for i in cols:
            d[i] = df[i]

        return d
    
    def set_index(self,df):
        df = df 
        l = self.df_len(df)
        df['index'] = [i for i in range(l)]

        return df

    
    def filter(self,df,columns,conditions,values,seperators=[]):
        df = self.set_index(df) 

        d = {}
        all_idx = list(df['index'])
        if len(seperators) < len(columns):
            seperators = seperators + ['and'] * (len(columns) - len(seperators))
        for col,cond,val,sep in zip(columns,conditions,values,seperators):

            cur_col_values = df[col]
            
            cur_idx = []
            for i,j in enumerate(cur_col_values):
                if col not in ['movieId','year','userId','rating']:
                    j = j.lower()
                    val = val.lower()
                if cond == '=':
                    if j == val:
                        cur_idx.append(df['index'][i])
                
                elif cond == '>':
                    if j > val:
                        cur_idx.append(df['index'][i])
                
                elif cond == '<':
                    if j <val:
                        cur_idx.append(df['index'][i])

                elif cond == '>=':
                    if j >=val:
                        cur_idx.append(df['index'][i])

                elif cond == '<=':
                    if j<=val:
                        cur_idx.append(df['index'][i])

                elif cond == '!=':
                    if j !=val:
                        cur_idx.append(df['index'][i])

                else:
                    print('invalid condition')
                    return

            if sep.lower() == 'and':
                for i in all_idx[:]:
                    if i not in cur_idx:
                        all_idx.remove(i)
            
            if sep.lower() == 'or':
                for i in cur_idx:
                    if i not in all_idx:
                        all_idx.append(i)

        all_idx.sort()

        for c in df.keys():
            if c!='index':

                for i in all_idx:
                    d.setdefault(c,[]).append(df[c][i])

        return d
        



            
        

