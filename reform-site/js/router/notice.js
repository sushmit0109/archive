    'use strict';

    angular.module('app')
        .config(function ($stateProvider) {
            $stateProvider
                .state('notice', {
                    parent: 'site',
                    url: '/notice',
                    data: {
                        authorities: []
                    },
                    views: {
                        'content@': {
                            templateUrl: './views/notice/list.html',
                            controller: 'NoticeController'
                        }
                    }
                })
                .state('view-notice', {
                    parent: 'site',
                    url: '/view-notice/{id}',
                    data: {
                        authorities: []
                    },
                    views: {
                        'content@': {
                            templateUrl: './views/notice/view.html',
                            controller: 'NoticeViewController'
                        }
                    }
                })
        });
