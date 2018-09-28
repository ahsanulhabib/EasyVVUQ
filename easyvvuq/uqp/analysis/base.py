import easyvvuq.utils.json as json_utils
from pandas import DataFrame
from easyvvuq import Campaign

__copyright__ = """

    Copyright 2018 Robin A. Richardson, David W. Wright 

    This file is part of EasyVVUQ 

    EasyVVUQ is free software: you can redistribute it and/or modify
    it under the terms of the Lesser GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    EasyVVUQ is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    Lesser GNU General Public License for more details.

    You should have received a copy of the Lesser GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
__license__ = "LGPL"


class BaseAnalysisUQP(object):
    """Baseclass for all EasyVVUQ analysis UQPs.

    Parameters
    ----------
    data_src    : dict or Campaign or stream
        Information on the infomration Application information. Will try interpreting as a dict or JSON
        file/stream or filename.


    Attributes
    ----------

    """

    def __init__(self, data_src, *args, **kwargs):

        self.data_frame = None
        self.data = None

        if isinstance(data_src, Campaign):
            self.data_src = data_src.data
        elif isinstance(data_src, dict):
            self.data_src = data_src
        elif isinstance(data_src, DataFrame):
            self.data_frame = data_src
        else:
            self.data_src = json_utils.process_json(data_src)
