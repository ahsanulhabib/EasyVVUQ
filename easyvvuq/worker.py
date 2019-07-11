import os
import logging
import json
import easyvvuq
from easyvvuq import ParamsSpecification
from easyvvuq.constants import default_campaign_prefix, Status
from easyvvuq.data_structs import RunInfo, CampaignInfo, AppInfo
from easyvvuq.sampling import BaseSamplingElement
from easyvvuq.collate import BaseCollationElement

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


logger = logging.getLogger(__name__)


class Worker:
    def __init__(
            self,
            db_type="sql",
            db_location=None,
            campaign_name=None,
            app_name=None
    ):

        self.campaign_name = campaign_name
        self.db_type = db_type
        self.db_location = db_location

        if self.db_type == 'sql':
            from .db.sql import CampaignDB
        elif self.db_type == 'json':
            from .db.json import CampaignDB
        else:
            message = (f"Invalid 'db_type' {self.db_type}. Supported types "
                       f"are 'sql' or 'json'.")
            logger.critical(message)
            raise RuntimeError(message)

        # Open session to the database
        logger.info(f"Opening session with CampaignDB at {self.db_location}")
        self.campaign_db = CampaignDB(location=self.db_location,
                                      new_campaign=False,
                                      name=self.campaign_name)
        self.campaign_id = self.campaign_db.get_campaign_id(self.campaign_name)

        # Resurrect the app encoder and decoder elements
        self._active_app_name = app_name
        self._active_app = self.campaign_db.app(name=app_name)
        (self._active_app_encoder,
         self._active_app_decoder) = self.campaign_db.resurrect_app(app_name)

    def encode_runs(self, run_id_list):

        # Get the encoder for this app. If none is set, only the directory structure
        # will be created.
        active_encoder = self._active_app_encoder
        if active_encoder is None:
            logger.warning('No encoder set for this app. Creating directory structure only.')
        else:
            use_fixtures = active_encoder.fixture_support
            fixtures = self._active_app['fixtures']

        # Loop through all runs in the run_id_list
        runs_dir = self.campaign_db.runs_dir()
        for run_id in run_id_list:

            run_data = self.campaign_db.run(run_id)

            # Make run directory
            target_dir = os.path.join(runs_dir, run_id)
            os.makedirs(target_dir)
            self.campaign_db.set_dir_for_run(run_id, target_dir)

            if active_encoder is not None:
                if use_fixtures:
                    active_encoder.encode(params=run_data['params'],
                                          fixtures=fixtures,
                                          target_dir=target_dir)
                else:
                    active_encoder.encode(params=run_data['params'],
                                          target_dir=target_dir)

        # Update run statuses in db
        self.campaign_db.set_run_statuses(run_id_list, Status.ENCODED)

    def call_for_each_run(self, fn, status=Status.ENCODED):

        # Loop through all runs in this campaign with the specified status,
        # and call the specified user function for each.
        for run_id, run_data in self.campaign_db.runs(status=status):
            fn(run_data['run_dir'], run_data['params'])
