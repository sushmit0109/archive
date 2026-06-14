'use strict';

angular.module('app')
    .factory('AllChapter', function ($http) {
        return {
            get: function (callback) {
                if (callback) callback([]);
            }
        };
    })
    .factory('ChapterByCommission', function ($http) {
        return {
            get: function (params, callback) {
                $http.get('./api-data/chapters-commission-' + params.id + '.json').then(function (response) {
                    var data = response.data;
                    if (params.searchKey) {
                        var key = params.searchKey.toLowerCase();
                        data = data.filter(function (ch) {
                            return (ch.title && ch.title.toLowerCase().indexOf(key) >= 0) ||
                                   (ch.nameBangla && ch.nameBangla.toLowerCase().indexOf(key) >= 0);
                        });
                    }
                    if (callback) callback(data);
                });
            }
        };
    });
