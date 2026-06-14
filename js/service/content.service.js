'use strict';

angular.module('app')
    .factory('Content', function ($http, $resource) {
        return $resource('api/content/:id', {}, {
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
    }).factory('AllContent', function ($http, $resource) {
    return $resource('./api/content/find-all', {}, {
        'get': {
            method: 'GET', headers: {'Content-Type': 'application/json'}, params: {}, format: 'json',
            transformResponse: [function (data, headersGetter) {
                console.log(data);
                return data;
            }].concat($http.defaults.transformResponse)
        }
    })
}).factory('ChapterWiseContent', function ($http, $resource) {
    return $resource('./api/content/chapter-wise', {}, {
        'get': {
            method: 'GET', headers: {'Content-Type': 'application/json'}, params: {}, format: 'json', isArray:true,
            transformResponse: [function (data, headersGetter) {
                console.log(data);
                return data;
            }].concat($http.defaults.transformResponse)
        }
    })
}).factory('PaginationContent', function ($http, $resource) {
    return $resource('./api/content/page/:page_num', {}, {
        'get': {
            method: 'GET', params: {}, format: 'json',
            transformResponse: [function (data, headersGetter) {
                return data;
            }].concat($http.defaults.transformResponse)
        }
    });
}).factory('DeleteContent', function ($http, $resource) {
    return $resource('./api/content/delete/:id', {}, {
        'delete': {
            method: 'GET', params: {}, format: 'json',
            transformResponse: [function (data, headersGetter) {
                return data;
            }].concat($http.defaults.transformResponse)
        }
    });
}).factory('MaxSerialBySection', function ($http, $resource) {
    return $resource('./api/content/max-serial/:sectionId', {}, {
        'get': {
            method: 'GET', params: {}, format: 'json',
            transformResponse: [function (data, headersGetter) {
                return data;
            }].concat($http.defaults.transformResponse)
        }
    });
})
;


