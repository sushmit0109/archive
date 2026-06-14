'use strict';

angular.module('app')
    .factory('Book', function ($http) {
        return {
            get: function (params, callback) {
                $http.get('./api-data/books.json').then(function (response) {
                    var book = response.data.filter(function (b) { return b.id == params.id; })[0];
                    if (callback) callback(book);
                });
            }
        };
    })
    .factory('AllBook', function ($http) {
        return {
            get: function (callback) {
                $http.get('./api-data/books.json').then(function (response) {
                    if (callback) callback(response.data);
                });
            }
        };
    });
