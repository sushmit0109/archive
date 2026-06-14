'use strict';

angular.module('app')
    .factory('Volume', function ($http) {
        return {
            get: function (params, callback) {
                if (callback) callback({});
            }
        };
    })
    .factory('VolumeWiseChapterByCommission', function ($http) {
        return {
            get: function (params, callback) {
                $http.get('./api-data/volume-wise-commission-' + params.id + '.json').then(function (response) {
                    if (callback) callback(response.data);
                });
            }
        };
    })
    .factory('VolumeByCommission', function ($http) {
        return {
            get: function (params, callback) {
                $http.get('./api-data/volumes-commission-' + params.id + '.json').then(function (response) {
                    if (callback) callback(response.data);
                });
            }
        };
    });
