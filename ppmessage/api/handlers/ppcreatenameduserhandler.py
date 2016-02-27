# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2016 PPMessage.
# Guijin Ding, dingguijin@gmail.com
#
#

from .basehandler import BaseHandler

from ppmessage.db.models import DeviceUser
from ppmessage.db.models import AppUserData
from ppmessage.core.constant import USER_STATUS
from ppmessage.core.constant import PPMESSAGE_APP
from ppmessage.core.redis import redis_hash_to_dict

from ppmessage.api.error import API_ERR

import json
import logging
import uuid

class PPGetUserUUIDHandler(BaseHandler):
    """
    requst:
    header
    user_email

    response:
    error_code

    """
    def _create_third_party(self, _user_email, _user_fullname, _user_icon):
        _redis = self.application.redis
        _du_uuid = str(uuid.uuid1())
        _values = {
            "uuid": _du_uuid,
            "user_status": USER_STATUS.THIRDPARTY,
            "user_name": _user_email,
            "user_email": _user_email,
            "user_fullname": _user_fullname,
            "is_anonymous_user": False,
        }
        if _user_icon != None:
            _values["user_icon"] = _user_icon

        _row = DeviceUser(**_values)
        _row.async_add()
        _row.create_redis_keys(_redis)
        
        _data_uuid = str(uuid.uuid1())
        _values = {
            "uuid": _data_uuid,
            "user_uuid": _du_uuid,
            "app_uuid": self.app_uuid,
            "is_portal_user": True,
            "is_service_user": False,
            "is_owner_user": False,
            "is_distributor_user": False,
        }
        _row = AppUserData(**_values)
        _row.async_add()
        _row.create_redis_keys(_redis)

        _r = self.getReturnData()
        _r["user_uuid"] = _du_uuid
        return
    
    def _get(self, _user_email, _user_fullname, _user_icon):
        _redis = self.application.redis
        _key = DeviceUser.__tablename__ + ".user_email." + _user_email
        _uuid = _redis.get(_key)
        if _uuid == None:
            self._create_third_party(_user_email, _user_fullname, _user_icon)
            return

        _key = AppUserData.__tablename__ + ".app_uuid." +  self.app_uuid + ".user_uuid." + _uuid + ".is_service_user.True"
        
        if _redis.exists(_key):
            logging.error("user is service user who can not help himself ^_^.")
            self.setErrorCode(API_ERR.NOT_PORTAL)
            return
       
        _r = self.getReturnData()
        _r["user_uuid"] = _uuid
        return

    def _Task(self):
        super(PPGetUserUUIDHandler, self)._Task()
        _request = json.loads(self.request.body)
        _user_email = _request.get("user_email")
        _user_fullname = _request.get("user_fullname")
        _user_icon = _request.get("user_icon")
        
        if _user_email == None:
            logging.error("no user_eamil provided.")
            self.setErrorCode(API_ERR.NO_PARA)
            return

        if _user_fullname == None:
            _user_fullname = _user_email.split("@")[0]

        self._get(_user_email, _user_fullname, _user_icon)
        return
