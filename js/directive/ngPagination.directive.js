
angular.module('app')
    .directive('ngPagination',['$compile', function ($compile) {
        return {
            restrict: 'A',
            terminal: true,
            priority: 100001,
            link: function link(scope,element, attrs) {
                element.after('<div align="center">' +
                    '<pagination ng-model="currentPage"'+
                    'total-items="totalElement"'+
                    'max-size="maxSize"'+
                    'boundary-links="true">'+
                    '</pagination></div>');
                $compile(element)(scope);
            }
        };
    }]);