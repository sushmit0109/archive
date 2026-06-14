'use strict';

angular.module('app')
    .factory('Section', function ($http, $resource) {
        return $resource('./api/section/:id', {}, {
            'get': {
                method: 'GET', headers: {'Content-Type': 'application/json'}, params: {}, format: 'json',
                transformResponse: [function (data, headersGetter) {
                    console.log(data);
                    return data;
                }].concat($http.defaults.transformResponse)
            },
            'save': {
                method: 'POST', headers: {'Content-Type': 'application/json'}, params: {}, format: 'json', isArray:true,
                transformResponse: [function (data, headersGetter) {
                    console.log(data);
                    return data;
                }].concat($http.defaults.transformResponse)
            },
            'update': {
                method: 'PUT', params: {}, format: 'json',
                transformResponse: [function (data, headersGetter) {
                    console.log(data);
                    return data;
                }].concat($http.defaults.transformResponse)
            },
            'delete': {
                method: 'DELETE', params: {}, format: 'json',
                transformResponse: [function (data, headersGetter) {
                    console.log(data);
                    return data;
                }].concat($http.defaults.transformResponse)
            }
        });
    }).factory('AllSection', function ($http, $resource) {
    return $resource('./api/section/find-all', {}, {
        'get': {
            method: 'GET', headers: {'Content-Type': 'application/json'}, params: {}, format: 'json',isArray:true,
            transformResponse: [function (data, headersGetter) {
                console.log(data);
                return data;
            }].concat($http.defaults.transformResponse)
        }
    })
}).factory('PaginationSection', function ($http, $resource) {
    return $resource('./api/section/page/:page_num', {}, {
        'get': {
            method: 'GET', params: {}, format: 'json',
            transformResponse: [function (data, headersGetter) {
                return data;
            }].concat($http.defaults.transformResponse)
        }
    });
})
;


