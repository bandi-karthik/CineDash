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
                    try:
                        j = j.lower()
                        val = val.lower()
                    except AttributeError: # Handle if 'j' is a number
                        pass
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

            groups.setdefault(tuple(cur_row), []).append(i) # cur_row-values tuple : idx where it occured 
       
        d = {}
        
        for col, val_idx in groups.items():
            for i, col_name in enumerate(groupby_columns):
                d.setdefault(col_name, []).append(col[i]) 
                

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
                            try:
                                su = su + i
                            except TypeError: # Handle mixed types
                                su = su + float(i) 
                        d.setdefault(a_col + '_sum', []).append(su)

                    elif agg_type == 'avg':
                        su = 0
                        cnt = 0
                        
                        for i in agg_data:
                            cnt = cnt + 1 
                            try:
                                su = su + i
                            except TypeError:
                                su = su + float(i)

                        if cnt<1:
                            # return 'no records found to calcuate the average, zero divide error!'
                            d.setdefault(a_col+'_avg',[]).append(0) # Safer return
                        else:
                            d.setdefault(a_col+'_avg',[]).append(su/cnt)

                    elif agg_type == 'min':
                        if not agg_data:
                            min_val = None
                        else:
                            min_val = agg_data[0]
                        for i in agg_data:
                            if i<min_val:
                                min_val = i 
                        d.setdefault(a_col + '_min', []).append(min_val)
                    
                    elif agg_type == 'max':
                        if not agg_data:
                            max_val = None
                        else:
                            max_val = agg_data[0]
                        for i in agg_data:
                            if i>max_val:
                                max_val = i 
                        d.setdefault(a_col + '_max', []).append(max_val)

                    else:
                        return 'Not a valid aggregation type, choose from : sum, count, min, max, avg'
            except ValueError:
                return 'Datatype error check the aggregation columns, type usage!'
            except TypeError:
                return 'Datatype error check the aggregation columns, type usage!'

        return d 
        
    def join(self, df_left, df_right, on_columns, how='inner'):
        df_left = copy.deepcopy(df_left)
        df_right = copy.deepcopy(df_right)

        right_index = {}
        l_right = self.df_len(df_right)

        for i in range(l_right):
            cur_key_values = []
            for c in on_columns:
                cur_key_values.append(df_right[c][i])
            key = tuple(cur_key_values)
            right_index.setdefault(key, []).append(i)

        d = {} 
        
        d_cols = list(df_left.keys())
        for c in df_right.keys():
            if c not in on_columns:
                d_cols.append(c)

        for c in d_cols:
            d[c] = []

        used_right_indices = set() 
        l_left = self.df_len(df_left)
        
        for i in range(l_left):
            
            cur_key_values = []
            for c in on_columns:
                cur_key_values.append(df_left[c][i])
            key = tuple(cur_key_values)
            
            matched_right_indices = right_index.get(key)

            if matched_right_indices:
            
                for j in matched_right_indices:
                   
                    for c_left in df_left.keys():
                        d[c_left].append(df_left[c_left][i])
                    
                   
                    for c_right in df_right.keys():
                        if c_right not in on_columns:
                            d[c_right].append(df_right[c_right][j])
                    
                    used_right_indices.add(j) 

            elif how == 'left' or how == 'full':
                          
                for c_left in df_left.keys():
                    d[c_left].append(df_left[c_left][i])
                
                for c_right in df_right.keys():
                    if c_right not in on_columns:
                        d[c_right].append('None') 

        
        if how == 'right' or how == 'full':
            for i in range(l_right):
                if i not in used_right_indices:
                   
                    for c in d.keys():
                        if c in df_left.keys() and c not in on_columns:
                 
                            d[c].append('None')
                        elif c in on_columns:
                            
                            d[c].append(df_right[c][i])
                        elif c in df_right.keys():

                            d[c].append(df_right[c][i])

        return d