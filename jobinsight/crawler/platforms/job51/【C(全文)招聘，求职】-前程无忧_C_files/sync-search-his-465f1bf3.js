/* 跨页面搜索历史同步控制器 v3.1 */
(function (global) {
  'use strict';

  // ----------------- 配置中心 -----------------
  var _config = {
    syncEndpoints: ['https://www.51job.com/seoapi/sync-search-his.html', 'https://we.51job.com/seoapi/sync-search-his.html',],   // 可添加其他同步节点
    syncTimeout: 3000,              // 通信通道存活时间(ms)
    storageKey: 'searchText',  //存储在localstroage的key名
    searchKeyValueStorageKey: "searchKeyValue",  // searchKeyValue数据存储在localstorage的key名
  };

  if (!Object.assign)  {
    Object.assign  = function(target) {
      for (var i = 1; i < arguments.length;  i++) {
        var source = arguments[i];
        for (var key in source) {
          if (Object.prototype.hasOwnProperty.call(source,  key)) {
            target[key] = source[key];
          }
        }
      }
      return target;
    };
  }

  // ----------------- 安全增强版通信引擎 -----------------
  // URL解析兼容方案（IE9+）
  function _parseURL(url) {
    var a = document.createElement('a');
    a.href  = url;
    return {
      origin: a.protocol  + '//' + a.hostname,
      href: a.href
    };
  }

  // 白名单验证函数
  function _isValidEndpoint(url) {
    try {
      var parsed = _parseURL(url);
      return _config.syncEndpoints.some(function(endpoint)  {
        var safeEndpoint = endpoint.split('?')[0].split('#')[0];
        return parsed.href.indexOf(safeEndpoint)  === 0;
      });
    } catch (e) {
      console.error('URL  validation failed:', e);
      return false;
    }
  }

  // 增强版iframe通信通道
  var _createSyncChannel = (function () {
    var channelCounter = 0;
    return function (src) {
      if (!_isValidEndpoint(src)) {
        console.warn('[Security]  Blocked invalid sync endpoint:', src);
        return null;
      }

      var iframe = document.createElement('iframe');
      iframe.src  = src;
      iframe.dataset.channelId  = 'sync_ch_' + (++channelCounter);
      iframe.style.cssText  = [
        'position: fixed',
        'width: 0',
        'height: 0',
        'opacity: 0',
        'pointer-events: none'
      ].join(';');
      document.body.appendChild(iframe);
      return iframe;
    };
  })();

  function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      var r = Math.random()  * 16 | 0;
      var v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }
  /**
   * 手写HTTP请求工具（XMLHttpRequest实现）
   * @param {string} method 请求方法（GET/POST等）
   * @param {string} url 请求地址
   * @param {Object|null} data 请求数据（可选）
   * @param {Object} headers 请求头（可选）
   * @returns {Promise} 返回Promise对象
   */

  // 兼容方案
  function httpRequest(method, url, data, success, error) {
    var xhr = new XMLHttpRequest();
    xhr.open(method,  url, true);

    xhr.onload  = function() {
      if (xhr.status  >= 200 && xhr.status  < 300) {
        try {
          success(JSON.parse(xhr.responseText));
        } catch(e) {
          success(xhr.responseText);
        }
      } else {
        error(new Error('HTTP ' + xhr.status));
      }
    };

    xhr.onerror  = function() {
      error(new Error('Network error'));
    };

    if (data) {
      xhr.setRequestHeader('Content-Type',  'application/json');
      xhr.send(JSON.stringify(data));
    } else {
      xhr.send();
    }
  }


  function _cleanupChannel(iframe) {
    setTimeout(function() {
      if(iframe && iframe.parentElement) {
        iframe.parentElement.removeChild(iframe);
      }
    }, _config.syncTimeout);
  }

  function sanitize(input) {
    return String(input).replace(/[<>'"&]/g, '');
  }

  //----------------- 数据管理器 -----------------
  var _historyStore = {
    save: function (string) {
      try {
        if(JSON.stringify(localStorage).length  > 4.5*1024*1024) {
          this.clear();
        }
        localStorage.setItem(_config.storageKey, sanitize(string));
      } catch (e) {
        console.error('localStorage setItem failed:', e);
      }
    },
    saveKeyValue: function (string) {
      try {
        if(JSON.stringify(localStorage).length  > 4.5*1024*1024) {
          this.clear();
        }
        localStorage.setItem(_config.searchKeyValueStorageKey, JSON.stringify(string));
      } catch (e) {
        console.error('localStorage setItem failed:', e);
      }
    },

    load: function () {
      try {
        return JSON.parse(localStorage.getItem(_config.storageKey))  || [];
      } catch {
        return [];
      }
    },

    clear: function () {
      localStorage.removeItem(_config.storageKey);
      localStorage.removeItem(_config.searchKeyValueStorageKey);
    }
  };

  //----------------- 核心逻辑 -----------------
  // 兼容IE的页面判断
  function _isCurrentPage(url) {
    var current = _parseURL(location.href);
    var target = _parseURL(url);
    return target.origin  === current.origin;
  }
  function _broadcastSignal(params) {
    // 如果当前是iframe页面则不执行创建全站通信(iframe方式通知),防止清除动作递归调用!!!!
    if(location.href.indexOf('/sync-search-his.html') > -1) return
    if (!params || typeof params !== 'object') return; // 新增参数校验

    var timestamp = Date.now();
    _config.syncEndpoints.forEach(function(endpoint)  {
      if (!_isCurrentPage(endpoint)) {
        try {
          var url = _parseURL(endpoint).href;
          function _serializeParams(params) {
            return Object.keys(params).map(function(key)  {
              return encodeURIComponent(key) + '=' + encodeURIComponent(params[key]);
            }).join('&');
          }
          url += (url.indexOf('?')  > -1 ? '&' : '?') +
              _serializeParams(Object.assign({},  params, { _sync_ts: timestamp }));

          if (_isValidEndpoint(url)) {
            var iframe = _createSyncChannel(url); // 创建iframe
            _cleanupChannel(iframe);
          }
        } catch (e) {
          console.error('Broadcast  failed:', e);
        }
      }
    });
  }

  function _parseQueryString(query) {
    var params = {};
    (query || '').replace(/^\?/, '').split('&').forEach(function(pair) {
      if (!pair) return;
      var kv = pair.split('=');
      var key = decodeURIComponent(kv[0] || '');
      var value = decodeURIComponent(kv.slice(1).join('=')  || '');
      params[key] = value;
    });
    return params;
  }

  function _processURLParams() {
    var params = _parseQueryString(location.search);

    // 执行清除历史记录，则前置跳出
    if ('clearHistory' in params)  {
      _historyStore.clear();
      // todo当前域名若是we.51job.com则单独处理********************
      if(location.hostname == 'we.51job.com') {
        localStorage.setItem('searchhistory', '');
        localStorage.setItem('inputHistory', '');
      }
      _broadcastSignal({ clearHistory: 1 });
      return;
    }
    // query中有uuid则调用接口去拿searchKeyValue和searchText,并保存到localstorage中
    var uuid = params.uuid;
    if (uuid) {
      var apiUrl = 'https://www.51job.com/seoapi/sync-search-his-get?tsid='+ encodeURIComponent(uuid);
      // 调用接口
      httpRequest('GET', apiUrl, null,
          function(response) {
            // console.log('GET  成功:', response);
            if(response && response.searchText)  {
              _historyStore.save(response.searchText);
            }
            if(response && response.searchKeyValue)  {
              _historyStore.saveKeyValue(response.searchKeyValue);
            }
          },
          function(error) {
            console.warn(' 获取搜索记录失败:', error);
          }
      );
    }
  }



  //----------------- 公开接口 -----------------
  global.SearchHistorySync = {
    // 配置管理
    config: function (options) {
      Object.assign(_config,  options);
      return this;
    },

    syncSearchHistoryUuid: function (uuid) {
      if (uuid) {
        _broadcastSignal({ 'uuid': uuid });
      }
    },
    // 保存搜索记录并通过iframe同步数据到其他页面localstorage中
    saveHistoryByUUIDAndSyncAll: function (data = {}) {
      if (data && data.searchText && data.searchKeyValue ) {
        var self = this;
        httpRequest('POST', 'https://www.51job.com/seoapi/sync-search-his-post',
            data,
            function(response) {
              var uuid = response && response.data && response.data.tsid;
              // console.log(' 同步数据到接口成功:', response);
              if (response.code  === 0) {
                _historyStore.save(data.searchText);
                _historyStore.saveKeyValue(data.searchKeyValue);
                self.syncSearchHistoryUuid(uuid);
              }
            },
            function(error) {
              console.error('POST  失败:', error);
            }
        );
      } else {
        console.warn('未传入搜索历史，调用保存搜索记录失败')
      }
    },

    generateUUID: generateUUID,

    clearGlobally: function () {
      _historyStore.clear();
      _broadcastSignal({ clearHistory: 1 });
    },

    // 数据接口
    getHistory: _historyStore.load,

    // 初始化
    init: function () {
      _processURLParams();
      return this;
    }
  };

  // 自动初始化
  global.SearchHistorySync.init();

})(window);

// // 绑定搜索事件
// SearchHistorySync.syncSearchHistory("dddd(全文)|d(全文)|1(全文)|123123(全文)|123123123(全文)");

// // 清空全局历史记录
// SearchHistorySync.clearGlobally()
;
