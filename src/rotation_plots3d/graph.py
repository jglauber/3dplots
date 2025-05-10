import pandas as pd
import os
import datetime
import numpy as np
from numpy import ndarray
from typing import TypeAlias
import plotly.graph_objects as go
from scipy import stats
import json
from typing import overload
import rotation_plots3d.errors as errors
from pypetb import Repeatability
import matplotlib.pyplot as plt

NDArray: TypeAlias = ndarray

class ObjectTrackingAnimation:
    """
    A class to handle data in time with x, y, z, roll, pitch, yaw and generate a 3D plot.

    Attributes
    ----------
    input_path : str
        The input path containing the data files.
    df_list : list[df]
        the list of loaded dataframes.
    
    Methods
    ------- 
    load()
        loads data from the input_path into the class as a list of pandas dataframes.
    
    create_graph(filename, device='1')
        creates a plotly 3D scatterplot timeseries
    """

    def __init__(self, input_path: str = 'files', **kwargs):
        self.input_path = input_path
        self.df_list = []
        self.kwargs = kwargs

    def __repr__(self):
        return json.dumps(self.__dict__,ensure_ascii=False,indent=4)

    def load(self):
        """
        A method to load the formatted data and store as a class attribute.
        """

        csv_files = os.listdir(self.input_path)
        for csv_file in csv_files:
            elapsed_time = 0

            with open(f"{self.input_path}/{csv_file}", 'r') as f:
                start = f.readline().strip().replace('Start Time: ','')+'000'
                lines = f.readlines()
                end = lines[-1].replace('End Time: ','').strip('\n')+'000'
                elapsed_time = datetime.datetime.strptime(end,"%Y-%m-%d_%H-%M-%S.%f") - datetime.datetime.strptime(start,"%Y-%m-%d_%H-%M-%S.%f")

            elapsed_time = elapsed_time.total_seconds()

            df = pd.read_csv(f"{self.input_path}/{csv_file}", skiprows=1, header=None)
            df = df.iloc[:-1]
            df.columns = ["Device", "X", "Y", "Z", "Roll", "Pitch", "Yaw"]

            dff = df[df["Device"] == '1']
            rows = dff.shape[0]

            time_interval = elapsed_time / (rows - 1)

            s = df["Device"]

            time_list = []
            count = -1
            current_time = 0
            for item in s.values:
                if item == '1':
                    count += 1
                    current_time = count * time_interval
                    time_list.append(current_time)
                else:
                    time_list.append(current_time)

            df.insert(0,"Duration_s",time_list)
            
            self.df_list.append((csv_file,df))

    def create_graph(self, filename: str, device: str = '1',
                     camera_up:dict = {"x": 0, "y": 1, "z": 0},
                     camera_center:dict = {"x": 0, "y": 0, "z": 0},
                     camera_eye:dict = {"x": 1.4, "y": 0.75, "z": 1.1},
                     x_range:list = [1.5, 4.5],
                     y_range:list = [-2, 1],
                     z_range:list = [-3, 0],
                     graph_title:str = "untitled"):
        """
        A method to create a plotly 3D time series plot.

        Parameters
        ----------
        filename : str
            The filename containing processed data.
        device : str
            The device to plot (typically '1')
        """
        # handle kwargs in the class
        camera_up = camera_up
        if self.kwargs.get('camera_up') is not None:
            camera_up = self.kwargs.get('camera_up')

        camera_center = camera_center
        if self.kwargs.get('camera_center') is not None:
            camera_center = self.kwargs.get('camera_center')

        camera_eye = camera_eye
        if self.kwargs.get('camera_eye') is not None:
            camera_eye = self.kwargs.get('camera_eye')
        
        x_range = x_range
        if self.kwargs.get('x_range') is not None:
            x_range = self.kwargs.get('x_range')

        y_range = y_range
        if self.kwargs.get('y_range') is not None:
            y_range = self.kwargs.get('y_range')

        z_range = z_range
        if self.kwargs.get('z_range') is not None:
            z_range = self.kwargs.get('z_range')

        graph_title = graph_title
        if self.kwargs.get('graph_title') is not None:
            graph_title = self.kwargs.get('graph_title')

        # create the dataframe
        df = dict(self.df_list)[filename]
        df = df[df["Device"] == device]
        df = df.reset_index()
        times = df['Duration_s'].values
        t = times[0]
        time_interval = times[1]

        x_start = df[df['Duration_s']==t]['X'].values[0].item()
        
        y_start = df[df['Duration_s']==t]['Y'].values[0].item()
        z_start = df[df['Duration_s']==t]['Z'].values[0].item()
        u_start = df[df['Duration_s']==t]['Roll'].values[0].item()
        v_start = df[df['Duration_s']==t]['Pitch'].values[0].item()
        w_start = df[df['Duration_s']==t]['Yaw'].values[0].item()
        point = np.array([x_start, y_start, z_start])

        (x1, y1, z1) = rotate_axes(u_start,v_start,w_start,point)

        hovertemplate = f"""
<b>time</b>: {'{:.3f}'.format(t)} s<br><br>
<b>X</b>: {x_start} m<br>
<b>Y</b>: {y_start} m<br>
<b>Z</b>: {z_start} m<br><br>
<b>roll</b>: {u_start} rad<br>
<b>pitch</b>: {v_start} rad<br>
<b>yaw</b>: {w_start} rad<br>
"""

        fig = go.Figure(data=[go.Cone(x=[x_start], y=[y_start], z=[z_start],u=[z1[0]-x_start], v=[z1[1]-y_start], w=[z1[2]-z_start], name='device', sizemode="absolute", sizeref=0.5, showscale=False, hovertemplate=hovertemplate),
                            go.Scatter3d(x=[x_start,x1[0]], y=[y_start,x1[1]], z=[z_start,x1[2]], mode='lines', name="x'", line={'color': 'red', 'width': 3.5}),
                            go.Cone(x=[x1[0]],y=[x1[1]],z=[x1[2]],u=[x1[0]-x_start], v=[x1[1]-y_start], w=[x1[2]-z_start],hoverinfo='skip', sizemode='absolute', sizeref=0.05, colorscale=[[0,'red'],[1,'red']], showscale=False),
                            go.Scatter3d(x=[x_start,y1[0]], y=[y_start,y1[1]], z=[z_start,y1[2]], mode='lines', name="y'", line={'color': 'green', 'width': 3.5}),
                            go.Cone(x=[y1[0]],y=[y1[1]],z=[y1[2]],u=[y1[0]-x_start], v=[y1[1]-y_start], w=[y1[2]-z_start],hoverinfo='skip', sizemode='absolute', sizeref=0.05, colorscale=[[0,'green'],[1,'green']], showscale=False),
                            go.Scatter3d(x=[x_start,z1[0]], y=[y_start,z1[1]], z=[z_start,z1[2]], mode='lines', name="z'", line={'color': 'blue', 'width': 3.5}),
                            go.Cone(x=[z1[0]],y=[z1[1]],z=[z1[2]],u=[z1[0]-x_start], v=[z1[1]-y_start], w=[z1[2]-z_start],hoverinfo='skip', sizemode='absolute', sizeref=0.05, colorscale=[[0,'blue'],[1,'blue']], showscale=False),
                            ])
        
        frames = []
        steps = []
        for i,__time in enumerate(times):

            print(f"Processed Data {i+1}/{len(times)}",end='\r')

            x_new = df[df['Duration_s']==__time]['X'].values[0].item()
            y_new = df[df['Duration_s']==__time]['Y'].values[0].item()
            z_new = df[df['Duration_s']==__time]['Z'].values[0].item()
            u_new = df[df['Duration_s']==__time]['Roll'].values[0].item()
            v_new = df[df['Duration_s']==__time]['Pitch'].values[0].item()
            w_new = df[df['Duration_s']==__time]['Yaw'].values[0].item()
            new_point = np.array([x_new, y_new, z_new])

            (x1, y1, z1) = rotate_axes(u_new,v_new,w_new,new_point)

            hovertemplate = f"""
<b>time</b>: {'{:.3f}'.format(__time)} s<br><br>
<b>X</b>: {x_new} m<br>
<b>Y</b>: {y_new} m<br>
<b>Z</b>: {z_new} m<br><br>
<b>roll</b>: {u_new} rad<br>
<b>pitch</b>: {v_new} rad<br>
<b>yaw</b>: {w_new} rad<br>
"""

            frame = go.Frame(data=[go.Cone(x=[x_new], y=[y_new], z=[z_new],u=[z1[0]-x_new], v=[z1[1]-y_new], w=[z1[2]-z_new], name='device', sizemode="absolute", sizeref=0.5, showscale=False, hovertemplate=hovertemplate),
                            go.Scatter3d(x=[x_new,x1[0]], y=[y_new,x1[1]], z=[z_new,x1[2]], mode='lines', name="x'", line={'color': 'red', 'width': 3.5}),
                            go.Cone(x=[x1[0]],y=[x1[1]],z=[x1[2]],u=[x1[0]-x_new], v=[x1[1]-y_new], w=[x1[2]-z_new],hoverinfo='skip', sizemode='absolute', sizeref=0.05, colorscale=[[0,'red'],[1,'red']], showscale=False),
                            go.Scatter3d(x=[x_new,y1[0]], y=[y_new,y1[1]], z=[z_new,y1[2]], mode='lines', name="y'", line={'color': 'green', 'width': 3.5}),
                            go.Cone(x=[y1[0]],y=[y1[1]],z=[y1[2]],u=[y1[0]-x_new], v=[y1[1]-y_new], w=[y1[2]-z_new],hoverinfo='skip', sizemode='absolute', sizeref=0.05, colorscale=[[0,'green'],[1,'green']], showscale=False),
                            go.Scatter3d(x=[x_new,z1[0]], y=[y_new,z1[1]], z=[z_new,z1[2]], mode='lines', name="z'", line={'color': 'blue', 'width': 3.5}),
                            go.Cone(x=[z1[0]],y=[z1[1]],z=[z1[2]],u=[z1[0]-x_new], v=[z1[1]-y_new], w=[z1[2]-z_new],hoverinfo='skip', sizemode='absolute', sizeref=0.05, colorscale=[[0,'blue'],[1,'blue']], showscale=False),
                            ],name=str(__time))
            frames.append(frame)

            num_frames = len(times)//50
            if i % num_frames == 0:
                step = {
                    "method": "animate",
                    "value": __time,
                    "label": "{:.1f}".format(np.float16(__time)),
                    "args": [[__time],{"frame": {"duration": 300, "redraw": True},
                            "mode": "immediate", "transition": {"duration": 0}}]
                }
                steps.append(step)
            

        fig.frames = frames

        fig.update_layout(
            title={"text": graph_title},
            margin={'pad': 25},
            updatemenus=[{
                "type": "buttons",
                "buttons": [{"label": "\u23F5",
                            "method": "animate",
                            "args": [None,{"frame": {"duration": int(time_interval*100), "redraw": True},
                                           "fromcurrent": True, "transition": {"duration": 0}}]},
                            {"label": "\u23F8",
                            "method": "animate",
                            "args": [[None], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate", "transition": {"duration": 0}}]},
                ],
                "direction": "left",
                "pad": {"r": 10,"t":50},
                "showactive": False,
                "y": 0,
                "yanchor": "top",
                "font": {"size": 20}
                }],
            scene={"aspectratio": {"x": 1, "y": 1, "z": 1},
                "xaxis": {"range": x_range},
                "yaxis": {"range": y_range},
                "zaxis": {"range": z_range}
            },
            scene_camera={"up": camera_up,
                        "center": camera_center,
                        "eye": camera_eye
            },
            sliders=[{"active": 0, "xanchor": 'left', "currentvalue": {"prefix": "Time (s): ", "visible": True, "xanchor": "right"},
                      "transition": {"duration": 0, "easing": "cubic-in-out"}, "steps": steps}]
        )

        fig.show()

    @overload
    def compare_stats(self, filename: str, device: str = '1', datarange: list = [[0,0],[0,0]]):
        ...
    
    @overload
    def compare_stats(self, filename: list[str], device: list[str] = ['1','1'], datarange: list = [[0,0],[0,0]]):
        ...

    def compare_stats(self, filename, device, datarange: list = [[0,0],[0,0]]):
        """
        A function to compare basic stats for two data ranges.

        Parameters
        ----------
        filename : str
            The filename containing processed data.

        device : str
            The device to plot (typically '1')

        datarange : list
            The list of start and end times [[start_time_1, end_time_1],[start_time_2, end_time_2]] for data set.
        """
        # create a dict to hold the start / stop times for each dataset.
        time_dict = {}
        for i, data_range in enumerate(datarange):
            time_dict[f'{i}'] = {}
            time_dict[f'{i}']['start'] = data_range[0]
            time_dict[f'{i}']['end'] = data_range[1]
            # get dataframe from Class.

            if isinstance(filename,str):
                df = dict(self.df_list)[filename]
                df = df[df["Device"] == device]

            elif isinstance(filename,list):
                if len(filename) != len(datarange) or len(filename) != len(device):
                    raise errors.DataRangeFileMismatch(len(filename),len(datarange),len(device))
                df = dict(self.df_list)[filename[i]]
                df = df[df["Device"] == device[i]]

            df = df.reset_index()
            time_dict[f'{i}']['df'] = df

        VALUE_LIST = ['X','Y','Z','Roll','Pitch','Yaw']
        output_dict = {}

        for k, v in time_dict.items():
            output_dict[k] = {}
            dff = v['df'][(v['df']['Duration_s'] >= v['start']) & (v['df']['Duration_s'] < v['end'])]
            output_dict[k]['n_samples'] = len(dff)
            list_from_dff = dff.iloc[:,6:9].values.tolist()
            for item in VALUE_LIST:                
                output_dict[k][item] = dff[item].values
            output_dict[k]['x_prime'] = []
            output_dict[k]['y_prime'] = []
            output_dict[k]['z_prime'] = []
            for row in list_from_dff:
                x1,y1,z1 = rotate_axes(row[0],row[1],row[2])
                output_dict[k]['x_prime'].append(x1)
                output_dict[k]['y_prime'].append(y1)
                output_dict[k]['z_prime'].append(z1)      
    
        stats_list = []
        for key, value in output_dict.items():
            stats_dict = {}
            for k,v in value.items():
                stats_dict[k] = {}        
                if k == 'x_prime' or k == 'y_prime' or k == 'z_prime':
                    average = np.mean(v, axis=0).tolist()
                    stats_dict[k]['mean'] = average
                    std_dev = np.std(v, axis=0).tolist()
                    stats_dict[k]['std_dev'] = std_dev
                    stats_dict[k]['n_samples'] = output_dict[key]['n_samples']
                elif k != 'n_samples':
                    p_value = stats.normaltest(v).pvalue

                    # calculate the mean value
                    average = np.mean(v)
                    stats_dict[k]['mean'] = average

                    # calculate the standard deviation
                    std_dev = np.std(v)
                    stats_dict[k]['std_dev'] = std_dev
                    stats_dict[k]['n_samples'] = output_dict[key]['n_samples']

                    # null hypothesis is normality.
                    # if p < 0.05 reject null hypothesis and dist is not normal with 95% confidence.
                    # if p > 0.05 fail to reject null and dist is normal.
                    if p_value > 0.05:
                        stats_dict[k]['pass_norm_dist_test'] = True                    
                    else:
                        stats_dict[k]['pass_norm_dist_test'] = False
            stats_list.append(stats_dict)
            
        # calculate the x_prime, y_prime, z_prime axes from the average roll, pitch, and yaw angles
        for stat in stats_list:
            u_mean = stat['Roll']['mean']
            v_mean = stat['Pitch']['mean']
            w_mean = stat['Yaw']['mean']
            u_std = stat['Roll']['std_dev']
            v_std = stat['Pitch']['std_dev']
            w_std = stat['Yaw']['std_dev']
            x1, y1, z1 = rotate_axes(u_mean,v_mean,w_mean)
            stat['x_prime']['average_uvw'] = x1.tolist()
            stat['y_prime']['average_uvw'] = y1.tolist()
            stat['z_prime']['average_uvw'] = z1.tolist()

            res = error_propagation(u_mean,v_mean,w_mean,u_std,v_std,w_std)
            stat['x_prime']['average_uvw_error'] = res[0]
            stat['y_prime']['average_uvw_error'] = res[1]
            stat['z_prime']['average_uvw_error'] = res[2]
            

        # calculate angle theta between the vectors from previous stat and current stat.
        for key, current_stat in output_dict.items():
            if int(key) > 0:
                previous_stat = output_dict[f"{int(key)-1}"]
                stats_list[int(key)]['x_prime']['angle_of_shift_degrees_vs_prev'] = angle_between_vectors(stats_list[int(key)]['x_prime']['average_uvw'],stats_list[int(key)-1]['x_prime']['average_uvw'],in_degrees=True)
                stats_list[int(key)]['y_prime']['angle_of_shift_degrees_vs_prev'] = angle_between_vectors(stats_list[int(key)]['y_prime']['average_uvw'],stats_list[int(key)-1]['y_prime']['average_uvw'],in_degrees=True)
                stats_list[int(key)]['z_prime']['angle_of_shift_degrees_vs_prev'] = angle_between_vectors(stats_list[int(key)]['z_prime']['average_uvw'],stats_list[int(key)-1]['z_prime']['average_uvw'],in_degrees=True)

                (x_prime_theta_error,y_prime_theta_error, z_prime_theta_error)= theta_error_propagation(x_prime_initial=stats_list[int(key)-1]['x_prime']['average_uvw'],
                                                                x_prime_initial_err=stats_list[int(key)-1]['x_prime']['average_uvw_error'],
                                                                x_prime_final=stats_list[int(key)]['x_prime']['average_uvw'],
                                                                x_prime_final_err=stats_list[int(key)]['x_prime']['average_uvw_error'],
                                                                y_prime_initial=stats_list[int(key)-1]['y_prime']['average_uvw'],
                                                                y_prime_initial_err=stats_list[int(key)-1]['y_prime']['average_uvw_error'],
                                                                y_prime_final=stats_list[int(key)]['y_prime']['average_uvw'],
                                                                y_prime_final_err=stats_list[int(key)]['y_prime']['average_uvw_error'],
                                                                z_prime_initial=stats_list[int(key)-1]['z_prime']['average_uvw'],
                                                                z_prime_initial_err=stats_list[int(key)-1]['z_prime']['average_uvw_error'],
                                                                z_prime_final=stats_list[int(key)]['z_prime']['average_uvw'],
                                                                z_prime_final_err=stats_list[int(key)]['z_prime']['average_uvw_error'],
                                                                in_degrees=True
                                                                )
                stats_list[int(key)]['x_prime']['angle_of_shift_degrees_vs_prev_error'] = x_prime_theta_error
                stats_list[int(key)]['y_prime']['angle_of_shift_degrees_vs_prev_error'] = y_prime_theta_error
                stats_list[int(key)]['z_prime']['angle_of_shift_degrees_vs_prev_error'] = z_prime_theta_error

                stats_list[int(key)]['x_prime']['angle_of_shift_degrees_vs_initial'] = angle_between_vectors(stats_list[int(key)]['x_prime']['average_uvw'],stats_list[0]['x_prime']['average_uvw'],in_degrees=True)
                stats_list[int(key)]['y_prime']['angle_of_shift_degrees_vs_initial'] = angle_between_vectors(stats_list[int(key)]['y_prime']['average_uvw'],stats_list[0]['y_prime']['average_uvw'],in_degrees=True)
                stats_list[int(key)]['z_prime']['angle_of_shift_degrees_vs_initial'] = angle_between_vectors(stats_list[int(key)]['z_prime']['average_uvw'],stats_list[0]['z_prime']['average_uvw'],in_degrees=True)

                (x_prime_theta_error,y_prime_theta_error, z_prime_theta_error)= theta_error_propagation(x_prime_initial=stats_list[0]['x_prime']['average_uvw'],
                                                                x_prime_initial_err=stats_list[0]['x_prime']['average_uvw_error'],
                                                                x_prime_final=stats_list[int(key)]['x_prime']['average_uvw'],
                                                                x_prime_final_err=stats_list[int(key)]['x_prime']['average_uvw_error'],
                                                                y_prime_initial=stats_list[0]['y_prime']['average_uvw'],
                                                                y_prime_initial_err=stats_list[0]['y_prime']['average_uvw_error'],
                                                                y_prime_final=stats_list[int(key)]['y_prime']['average_uvw'],
                                                                y_prime_final_err=stats_list[int(key)]['y_prime']['average_uvw_error'],
                                                                z_prime_initial=stats_list[0]['z_prime']['average_uvw'],
                                                                z_prime_initial_err=stats_list[0]['z_prime']['average_uvw_error'],
                                                                z_prime_final=stats_list[int(key)]['z_prime']['average_uvw'],
                                                                z_prime_final_err=stats_list[int(key)]['z_prime']['average_uvw_error'],
                                                                in_degrees=True
                                                                )
                stats_list[int(key)]['x_prime']['angle_of_shift_degrees_vs_initial_error'] = x_prime_theta_error
                stats_list[int(key)]['y_prime']['angle_of_shift_degrees_vs_initial_error'] = y_prime_theta_error
                stats_list[int(key)]['z_prime']['angle_of_shift_degrees_vs_initial_error'] = z_prime_theta_error

                # statistical significance calc using Mann-Whitney U test for difference of means 
                for item in VALUE_LIST:
                    res = stats.mannwhitneyu(previous_stat[item],current_stat[item])

                    # null hypothesis is means are equal.
                    # if p < 0.05 reject null hypothesis and mean is not equal with 95% confidence.
                    # if p > 0.05 fail to reject null and mean is likely equal.
                    p_value = res[1]
                    if p_value < 0.05:
                        stats_list[int(key)][item]['mann_whitneyutest_result_vs_prev'] = 'Statistical Difference'
                    else:
                        stats_list[int(key)][item]['mann_whitneyutest_result_vs_prev'] = 'No Statistical Difference'

                    res = stats.mannwhitneyu(output_dict['0'][item],current_stat[item])

                    # null hypothesis is means are equal.
                    # if p < 0.05 reject null hypothesis and mean is not equal with 95% confidence.
                    # if p > 0.05 fail to reject null and mean is likely equal.
                    p_value = res[1]
                    if p_value < 0.05:
                        stats_list[int(key)][item]['mann_whitneyutest_result_vs_initial'] = 'Statistical Difference'
                    else:
                        stats_list[int(key)][item]['mann_whitneyutest_result_vs_initial'] = 'No Statistical Difference'

        return stats_list
        
    @overload
    def stats_dataframe(self, filename: str, device: str = '1', datarange: list = [[0,0],[0,0]]):
        ...

    @overload
    def stats_dataframe(self, filename: list[str], device: list[str] = ['1','1'], datarange: list = [[0,0],[0,0]]):
        ...

    def stats_dataframe(self, filename, device, datarange: list = [[0,0],[0,0]]):
        """
        Returns a dataframe for easier analysis.
        """

        if isinstance(filename,str):
            stats_list = self.compare_stats(filename,device,datarange)
        
        if isinstance(filename,list):
            stats_list = self.compare_stats(filename,device,datarange)

        df = pd.DataFrame()
        VALUE_LIST_NEW = ['X','Y','Z','Roll','Pitch','Yaw', "x_prime", "y_prime", "z_prime"]
        for item in VALUE_LIST_NEW:
            modified_stats_list = [[v for k,v in d.items() if k == item][0] for d in stats_list]
            df_new = pd.DataFrame.from_records(modified_stats_list)
            df_new.insert(0,'Parameter',item)
            df = pd.concat([df,df_new])
        
        return df
    
    def gage_repeatability(self, filename, device, datarange: list = [[0,0],[0,0]], reps: int = 2, events: int = 10):
        """
        Compute the gage repeatabilty metrics.
        """

        df = self.stats_dataframe(filename,device,datarange)

        x = df[df['Parameter'] == 'X']['mean'].values
        y = df[df['Parameter'] == 'Y']['mean'].values
        z = df[df['Parameter'] == 'Z']['mean'].values

        theta_values_x_prime = df[df['Parameter'] == 'x_prime']['angle_of_shift_degrees_vs_initial'].values
        theta_values_x_prime = theta_values_x_prime[1:len(theta_values_x_prime)]

        theta_values_y_prime = df[df['Parameter'] == 'y_prime']['angle_of_shift_degrees_vs_initial'].values
        theta_values_y_prime = theta_values_y_prime[1:len(theta_values_y_prime)]

        theta_values_z_prime = df[df['Parameter'] == 'z_prime']['angle_of_shift_degrees_vs_initial'].values
        theta_values_z_prime = theta_values_z_prime[1:len(theta_values_z_prime)]

        event = []
        for i in range(0,events):
            event += [i+1] * reps

        event_prime = event[:-1]

        df_x_prime = pd.DataFrame({'event': event_prime,
                   'theta': theta_values_x_prime})

        df_y_prime = pd.DataFrame({'event': event_prime,
                        'theta': theta_values_y_prime})

        df_z_prime = pd.DataFrame({'event': event_prime,
                        'theta': theta_values_z_prime})
        
        df_x = pd.DataFrame({'event': event,
                             'position': x})
        df_x['position'] = df_x['position'].astype(float)
        
        df_y = pd.DataFrame({'event': event,
                             'position': y})
        df_y['position'] = df_y['position'].astype(float)
        
        df_z = pd.DataFrame({'event': event,
                             'position': z})
        df_z['position'] = df_z['position'].astype(float)
        
        dataframes = [("x_prime Repeatability", df_x_prime, "theta"),
                      ("y_prime Repeatability", df_y_prime, "theta"),
                      ("z_prime Repeatability",df_z_prime, "theta"),
                      ("X Repeatabilty", df_x, "position"),
                      ("Y Repeatability", df_y, "position"),
                      ("Z Repeatability", df_z, "position")]


        call=[]

        for title,df,measurement in dataframes:
            #Build up the model
            dict_key={'1':'event','2':measurement}
            RModel=Repeatability.RNumeric(
                mydf_Raw=df,
                mydict_key=dict_key
                )
            #Solve it
            RModel.RSolve(bol_bias=True)
            #Check the calculation
            print(RModel.getLog())

            df_Result=RModel.RAnova()
            #Checking Anova table
            print(df_Result)
            #accesing one individual value
            print(f"Degree of freedom for part: {df_Result['DF'].loc['Part']}")

            df_Result=RModel.R_varTable()
            #Checking var. table
            print(df_Result)
            #accesing one individual value
            print('\nRepeatability RESULT:\n-------------------')

            dbl_RnR=df_Result['% Contribution'].loc['Gage Repeatability']
            print(f"Total Gage R&R: {dbl_RnR:.3f}")
            if dbl_RnR<1:
                print('<1% --> Acceptable measurement system')
            elif dbl_RnR>=1 and dbl_RnR<=9:
                print(
                    '1-9%--> It may be acceptable depending on application and cost'
                    )
            else:
                print(
                    '>9% --> Unacceptable measurement system, it must be improved'
                    )
                
            df_Result=RModel.R_SDTable()
            #Checking sd table
            print(df_Result)
            #accesing one individual value
            print('\nAutomotive Industry Action Group (AIAG) measurement system assessment:\n-------------------')

            dbl_R=df_Result['% Study Var'].loc['Gage Repeatability']
            print(f"Total Gage Repeatability factor: {dbl_R:.3f}")
            if dbl_R<10:
                print('<10% --> Acceptable measurement system')
            elif dbl_R>=10 and dbl_R<=30:
                print(
                    '10-30%--> It may be acceptable depending on application and cost'
                    )
            else:
                print(
                    '>30% --> Unacceptable measurement system, it must be improved'
                    )
                
            # call=RModel.R_RunChart()
            # plt.show()

            call.append(RModel.R_Report(report_name=title))
        plt.show()




def _generate_rotation_matrix(u: float, v: float, w: float) -> NDArray:
    """
    A function to generate the rotation matrix
    given roll, pitch, and yaw angles in radians.

    Parameters
    ----------
    u : float
        The roll angle in radians.
    v : float
        The pitch angle in radians.
    w : float
        The yaw angle in radians.

    Returns
    -------
    array
        the rotation matrix.
    """

    rot_x = np.array([[1, 0, 0],
                      [0, np.cos(u), -np.sin(u)],
                      [0, np.sin(u), np.cos(u)]])
    
    rot_y = np.array([[np.cos(v), 0, np.sin(v)],
                      [0, 1, 0],
                      [-np.sin(v), 0, np.cos(v)]]
                      )

    rot_z = np.array([[np.cos(w), -np.sin(w), 0],
                      [np.sin(w), np.cos(w), 0],
                      [0, 0, 1]])

    rot_zyx = np.linalg.multi_dot([rot_z, rot_y, rot_x])

    return rot_zyx


def rotate_axes(u: float, v: float, w: float, point: NDArray = np.array([0,0,0])) -> tuple[NDArray]:
    """
    A function that takes roll, pitch, yaw in radians and
    rotates x, y, z axes via the rotation matrix.

    Parameters
    ----------
    u : float
        The roll angle in radians.
    v : float
        The pitch angle in radians.
    w : float
        The yaw angle in radians.
    point : NDArray
        The point to offset the axes to.

    Returns
    -------
    array
        Rotated vectors in the original x, y, z vector space shifted to the point.
    """

    rot_zyx = _generate_rotation_matrix(u,v,w)
    x_axis = np.array([1,0,0]).reshape(3,1)
    y_axis = np.array([0,1,0]).reshape(3,1)
    z_axis = np.array([0,0,1]).reshape(3,1)

    rot_x = np.array(np.linalg.matmul(rot_zyx, x_axis).reshape(1,3).tolist()[0])
    rot_y = np.array(np.linalg.matmul(rot_zyx, y_axis).reshape(1,3).tolist()[0])
    rot_z = np.array(np.linalg.matmul(rot_zyx, z_axis).reshape(1,3).tolist()[0])

    shifted_rot_x = rot_x + point
    shifted_rot_y = rot_y + point
    shifted_rot_z = rot_z + point

    return (shifted_rot_x,shifted_rot_y,shifted_rot_z)

def error_propagation(u: float, v: float, w: float, sigma_u: float, sigma_v: float, sigma_w: float) -> list[NDArray]:
    """
    Calculates the propagation of variances given mean values and standard deviations for roll, pitch, and yaw
    """
    sigma_x_prime_x = np.abs((np.cos(v) * np.cos(w)))*np.sqrt(np.square(np.tan(v) * sigma_v) + np.square(np.tan(w) * sigma_w))
    sigma_x_prime_y = np.abs((np.cos(v) * np.sin(w)))*np.sqrt(np.square(np.tan(v) * sigma_v) + np.square(sigma_w / np.tan(w)))
    sigma_x_prime_z = np.abs((np.cos(v) * sigma_v))

    sigma_y_prime_x = np.sqrt((np.square(np.sin(u) * np.sin(v) * np.cos(w)) *
                       (np.square(sigma_u / np.tan(u)) + np.square(sigma_v / np.tan(v)) + np.square(sigma_w * np.tan(w))))
                       + (np.square(np.cos(u) * np.sin(w)) * (np.square(sigma_u * np.tan(u)) + np.square(sigma_w / np.tan(w)))))
    sigma_y_prime_y = np.sqrt((np.square(np.cos(u) * np.cos(w)) *
                        (np.square(np.tan(u) * sigma_u) + np.square(np.tan(w) * sigma_w))) +
                        (np.square(np.sin(u) * np.sin(v) * np.sin(w)) * (np.square(sigma_u / np.tan(u)) + np.square(sigma_v / np.tan(v)) + np.square(sigma_w / np.tan(w)))))
    sigma_y_prime_z = np.abs(np.sin(u) * np.cos(v)) * np.sqrt(np.square(sigma_u / np.tan(u)) + np.square(np.tan(v) * sigma_v))
    sigma_z_prime_x = np.sqrt((np.square(np.sin(u) * np.sin(w)) *
                               (np.square(sigma_u * np.tan(u)) + np.square(sigma_w / np.tan(w)))) +
                              (np.square(np.cos(u) * np.sin(v) * np.cos(w)) *
                               (np.square(np.tan(u) * sigma_u) + np.square(sigma_v / np.tan(v)) + np.square(np.tan(w) * sigma_w))))
    sigma_z_prime_y = np.sqrt((np.square(np.cos(u) * np.sin(v) * np.sin(w)) *
                               (np.square(np.tan(u) * sigma_u) + np.square(sigma_v / np.tan(v)) + np.square(sigma_w / np.tan(w)))) +
                               (np.square(np.sin(u) * np.cos(w)) *
                                (np.square(sigma_u / np.tan(u)) + np.square(sigma_w * np.tan(w)))))
    sigma_z_prime_z = np.sqrt(np.square(np.cos(u) * np.cos(v)) * (np.square(sigma_u * np.tan(u)) + np.square(sigma_v * np.tan(v))))

    return [[sigma_x_prime_x.item(),sigma_x_prime_y.item(),sigma_x_prime_z.item()],
            [sigma_y_prime_x.item(),sigma_y_prime_y.item(),sigma_y_prime_z.item()],
            [sigma_z_prime_x.item(), sigma_z_prime_y.item(),sigma_z_prime_z.item()]]

def theta_error_propagation(x_prime_initial: list, x_prime_final: list, y_prime_initial: list,
                            y_prime_final: list, z_prime_initial: list, z_prime_final: list,
                            x_prime_initial_err: list, x_prime_final_err: list, y_prime_initial_err: list,
                            y_prime_final_err: list, z_prime_initial_err: list, z_prime_final_err: list, in_degrees: bool = False):
    """
    Calculates the error associated with the angle between two vectors.
    """

    x_prime_cos_theta_error = (np.square(x_prime_initial[0]*x_prime_final[0]) * (np.square(x_prime_initial_err[0] / x_prime_initial[0]) + np.square(x_prime_final_err[0] / x_prime_final[0])) +
                                np.square(x_prime_initial[1]*x_prime_final[1]) * (np.square(x_prime_initial_err[1] / x_prime_initial[1]) + np.square(x_prime_final_err[1] / x_prime_final[1])) +
                                np.square(x_prime_initial[2]*x_prime_final[2]) * (np.square(x_prime_initial_err[2] / x_prime_initial[2]) + np.square(x_prime_final_err[2] / x_prime_final[2])))
    
    x_prime_theta_error = np.abs(-1/np.sqrt(1-np.square(x_prime_initial[0] * x_prime_final[0] + x_prime_initial[1] * x_prime_final[1] + x_prime_initial[2] * x_prime_final[2]))) * x_prime_cos_theta_error

    y_prime_cos_theta_error = (np.square(y_prime_initial[0]*y_prime_final[0]) * (np.square(y_prime_initial_err[0] / y_prime_initial[0]) + np.square(y_prime_final_err[0] / y_prime_final[0])) +
                                np.square(y_prime_initial[1]*y_prime_final[1]) * (np.square(y_prime_initial_err[1] / y_prime_initial[1]) + np.square(y_prime_final_err[1] / y_prime_final[1])) +
                                np.square(y_prime_initial[2]*y_prime_final[2]) * (np.square(y_prime_initial_err[2] / y_prime_initial[2]) + np.square(y_prime_final_err[2] / y_prime_final[2])))
    
    y_prime_theta_error = np.abs(-1/np.sqrt(1-np.square(y_prime_initial[0] * y_prime_final[0] + y_prime_initial[1] * y_prime_final[1] + y_prime_initial[2] * y_prime_final[2]))) * y_prime_cos_theta_error

    z_prime_cos_theta_error = (np.square(z_prime_initial[0]*z_prime_final[0]) * (np.square(z_prime_initial_err[0] / z_prime_initial[0]) + np.square(z_prime_final_err[0] / z_prime_final[0])) +
                                np.square(z_prime_initial[1]*z_prime_final[1]) * (np.square(z_prime_initial_err[1] / z_prime_initial[1]) + np.square(z_prime_final_err[1] / z_prime_final[1])) +
                                np.square(z_prime_initial[2]*z_prime_final[2]) * (np.square(z_prime_initial_err[2] / z_prime_initial[2]) + np.square(z_prime_final_err[2] / z_prime_final[2])))
    
    z_prime_theta_error = np.abs(-1/np.sqrt(1-np.square(z_prime_initial[0] * z_prime_final[0] + z_prime_initial[1] * z_prime_final[1] + z_prime_initial[2] * z_prime_final[2]))) * z_prime_cos_theta_error

    if in_degrees:
        x_prime_theta_error = x_prime_theta_error * 180 / np.pi
        y_prime_theta_error = y_prime_theta_error * 180 / np.pi
        z_prime_theta_error = z_prime_theta_error * 180 / np.pi

    return (x_prime_theta_error, y_prime_theta_error, z_prime_theta_error)


def angle_between_vectors(a:NDArray, b:NDArray, in_degrees: bool = False) -> float:
    """
    Calculate the angle theta between two vectors using the dot product.
    """
    theta_rad = np.acos(np.dot(a,b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    if in_degrees:
        theta_deg = theta_rad * (180 / np.pi)
        return theta_deg
    else:
        return theta_rad