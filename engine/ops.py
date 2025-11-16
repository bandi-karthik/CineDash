import copy

class functions:

    def df_len(self,df):
        
        return len(df[list(df.keys())[0]])

    def head(self,df,limit=None,offset=0):
        d = {}

        for i in df.keys():
            if limit:
                d[i] = df[i][offset:limit+offset]
            else:
                d[i] = df[i][offset:5+offset]

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
        df = copy.deepcopy(df)
        l = self.df_len(df)
        df['index'] = [i for i in range(l)]

        return df

    
    def filter(self,df,columns,conditions,values,seperators=[]):
        df = copy.deepcopy(df)
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
                    return 'invalid condition'
                    

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

    def order_rows(self,df,cols,type='asc',limit=None):
        df = copy.deepcopy(df)
        df = df 
        if type == 'dsc':
            d= {}
            for c in cols:
                cur_col_vals = df[c]
                idx_d = {}
                for i,j in enumerate(cur_col_vals):
                    idx_d[i] = j 
                
                idx = dict(sorted(idx_d.items(), key=lambda x:x[1],reverse=True))
                #print(idx)
                idx = list(idx.keys())
                #print(idx)
                for c in df.keys():
                    for i in idx:
                        d.setdefault(c,[]).append(df[c][i])
            if limit:
                d = self.head(d,limit)

            return d
        else:
            return df
        
    
    def groupby(self, df, groupby_columns, agg_column, agg_type):
        
        groups = {}
        l = self.df_len(df)

        for i in range(l):

            cur_row = []
            for c in groupby_columns:
                cur_row.append(df[c][i])

            groups.setdefault(tuple(cur_row), []).append(i) # {(1995,): [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}
       
        d = {}
        
        for col, val_idx in groups.items():
            for i, col_name in enumerate(groupby_columns):
                d.setdefault(col_name, []).append(col[i]) #{'year':['1995']}
                

            try:
                for a_col in agg_column:
                    agg_data = []
                    for idx in val_idx:
                        agg_data.append(df[a_col][idx])


                    if agg_type == 'count':
                        cnt = 0
                        for i in agg_data:
                            cnt = cnt + 1 
                        d.setdefault(a_col+'_count',[]).append(cnt)
                    
                    elif agg_type == 'sum':
                        su = 0
                        for i in agg_data:
                            su = su + i
                        d.setdefault(a_col + '_sum', []).append(su)

                    elif agg_type == 'avg':
                        su = 0
                        cnt = 0
                        
                        for i in agg_data:
                            cnt = cnt + 1 
                            su = su + i

                        if cnt<1:
                            return 'no records found to calcuate the average, zero divide error!'
                                
                        d.setdefault(a_col+'_avg',[]).append(su/cnt)

                    elif agg_type == 'min':
                        min_val = agg_data[0]
                        for i in agg_data:
                            if i<min_val:
                                min_val = i 
                        
                        if min_val ==float('inf'):
                            return 'no records to find the min'
                            
                        d.setdefault(a_col + '_min', []).append(min_val)
                    
                    elif agg_type == 'max':
                        max_val = agg_data[0]
                        for i in agg_data:
                            if i>max_val:
                                max_val = i 
                        
                        if max_val ==float('-inf'):
                            return 'no records to find the min'
                            
                        d.setdefault(a_col + '_max', []).append(max_val)

                    else:
                        return 'Not a valid aggregation type, choose from : sum, count, min, max, avg'
            except ValueError:
                return 'Datatype error check the aggregation columns, type usage!'
            except TypeError:
                return 'Datatype error check the aggregation columns, type usage!'

        return d 
        

