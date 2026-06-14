'use strict';

angular.module('app')
    .factory('Notice', function ($http, $q) {
        var cachedNotices = null;

        function loadAll() {
            if (cachedNotices) return $q.resolve(cachedNotices);
            return $q.all([
                $http.get('./api-data/notices-page1.json'),
                $http.get('./api-data/notices-page2.json')
            ]).then(function (results) {
                cachedNotices = [];
                results.forEach(function (r) {
                    if (r.data && r.data.content) {
                        cachedNotices = cachedNotices.concat(r.data.content);
                    }
                });
                return cachedNotices;
            });
        }

        return {
            get: function (params, callback) {
                if (typeof params === 'function') { callback = params; params = {}; }

                if (params.id) {
                    loadAll().then(function (notices) {
                        var notice = notices.filter(function (n) { return n.id == params.id; })[0];
                        if (callback) callback(notice || {});
                    });
                } else {
                    var pageNum = params.pageNumber || 1;
                    $http.get('./api-data/notices-page' + pageNum + '.json').then(function (response) {
                        if (callback) callback(response.data);
                    });
                }
            }
        };
    });
