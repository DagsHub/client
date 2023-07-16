var __defProp = Object.defineProperty;
var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, {
  enumerable: true,
  configurable: true,
  writable: true,
  value
}) : obj[key] = value;
var __publicField = (obj, key, value) => {
  __defNormalProp(obj, typeof key !== "symbol" ? key + "" : key, value);
  return value;
};
(function (factory) {
  typeof define === "function" && define.amd ? define(factory) : factory();
})(function () {
  "use strict";
  var commonjsGlobal = typeof globalThis !== "undefined" ? globalThis : typeof window !== "undefined" ? window : typeof global !== "undefined" ? global : typeof self !== "undefined" ? self : {};
  var lodash = {exports: {}};
  /**
   * @license
   * Lodash <https://lodash.com/>
   * Copyright OpenJS Foundation and other contributors <https://openjsf.org/>
   * Released under MIT license <https://lodash.com/license>
   * Based on Underscore.js 1.8.3 <http://underscorejs.org/LICENSE>
   * Copyright Jeremy Ashkenas, DocumentCloud and Investigative Reporters & Editors
   */
  (function (module, exports) {
    (function () {
      var undefined$1;
      var VERSION = "4.17.21";
      var LARGE_ARRAY_SIZE = 200;
      var CORE_ERROR_TEXT = "Unsupported core-js use. Try https://npms.io/search?q=ponyfill.",
        FUNC_ERROR_TEXT = "Expected a function",
        INVALID_TEMPL_VAR_ERROR_TEXT = "Invalid `variable` option passed into `_.template`";
      var HASH_UNDEFINED = "__lodash_hash_undefined__";
      var MAX_MEMOIZE_SIZE = 500;
      var PLACEHOLDER = "__lodash_placeholder__";
      var CLONE_DEEP_FLAG = 1, CLONE_FLAT_FLAG = 2, CLONE_SYMBOLS_FLAG = 4;
      var COMPARE_PARTIAL_FLAG = 1, COMPARE_UNORDERED_FLAG = 2;
      var WRAP_BIND_FLAG = 1, WRAP_BIND_KEY_FLAG = 2, WRAP_CURRY_BOUND_FLAG = 4, WRAP_CURRY_FLAG = 8,
        WRAP_CURRY_RIGHT_FLAG = 16, WRAP_PARTIAL_FLAG = 32, WRAP_PARTIAL_RIGHT_FLAG = 64, WRAP_ARY_FLAG = 128,
        WRAP_REARG_FLAG = 256, WRAP_FLIP_FLAG = 512;
      var DEFAULT_TRUNC_LENGTH = 30, DEFAULT_TRUNC_OMISSION = "...";
      var HOT_COUNT = 800, HOT_SPAN = 16;
      var LAZY_FILTER_FLAG = 1, LAZY_MAP_FLAG = 2, LAZY_WHILE_FLAG = 3;
      var INFINITY = 1 / 0, MAX_SAFE_INTEGER = 9007199254740991, MAX_INTEGER = 17976931348623157e292, NAN = 0 / 0;
      var MAX_ARRAY_LENGTH = 4294967295, MAX_ARRAY_INDEX = MAX_ARRAY_LENGTH - 1,
        HALF_MAX_ARRAY_LENGTH = MAX_ARRAY_LENGTH >>> 1;
      var wrapFlags = [
        ["ary", WRAP_ARY_FLAG],
        ["bind", WRAP_BIND_FLAG],
        ["bindKey", WRAP_BIND_KEY_FLAG],
        ["curry", WRAP_CURRY_FLAG],
        ["curryRight", WRAP_CURRY_RIGHT_FLAG],
        ["flip", WRAP_FLIP_FLAG],
        ["partial", WRAP_PARTIAL_FLAG],
        ["partialRight", WRAP_PARTIAL_RIGHT_FLAG],
        ["rearg", WRAP_REARG_FLAG]
      ];
      var argsTag = "[object Arguments]", arrayTag = "[object Array]", asyncTag = "[object AsyncFunction]",
        boolTag = "[object Boolean]", dateTag = "[object Date]", domExcTag = "[object DOMException]",
        errorTag = "[object Error]", funcTag = "[object Function]", genTag = "[object GeneratorFunction]",
        mapTag = "[object Map]", numberTag = "[object Number]", nullTag = "[object Null]",
        objectTag = "[object Object]", promiseTag = "[object Promise]", proxyTag = "[object Proxy]",
        regexpTag = "[object RegExp]", setTag = "[object Set]", stringTag = "[object String]",
        symbolTag = "[object Symbol]", undefinedTag = "[object Undefined]", weakMapTag = "[object WeakMap]",
        weakSetTag = "[object WeakSet]";
      var arrayBufferTag = "[object ArrayBuffer]", dataViewTag = "[object DataView]",
        float32Tag = "[object Float32Array]", float64Tag = "[object Float64Array]", int8Tag = "[object Int8Array]",
        int16Tag = "[object Int16Array]", int32Tag = "[object Int32Array]", uint8Tag = "[object Uint8Array]",
        uint8ClampedTag = "[object Uint8ClampedArray]", uint16Tag = "[object Uint16Array]",
        uint32Tag = "[object Uint32Array]";
      var reEmptyStringLeading = /\b__p \+= '';/g, reEmptyStringMiddle = /\b(__p \+=) '' \+/g,
        reEmptyStringTrailing = /(__e\(.*?\)|\b__t\)) \+\n'';/g;
      var reEscapedHtml = /&(?:amp|lt|gt|quot|#39);/g, reUnescapedHtml = /[&<>"']/g,
        reHasEscapedHtml = RegExp(reEscapedHtml.source), reHasUnescapedHtml = RegExp(reUnescapedHtml.source);
      var reEscape = /<%-([\s\S]+?)%>/g, reEvaluate = /<%([\s\S]+?)%>/g, reInterpolate = /<%=([\s\S]+?)%>/g;
      var reIsDeepProp = /\.|\[(?:[^[\]]*|(["'])(?:(?!\1)[^\\]|\\.)*?\1)\]/, reIsPlainProp = /^\w*$/,
        rePropName = /[^.[\]]+|\[(?:(-?\d+(?:\.\d+)?)|(["'])((?:(?!\2)[^\\]|\\.)*?)\2)\]|(?=(?:\.|\[\])(?:\.|\[\]|$))/g;
      var reRegExpChar = /[\\^$.*+?()[\]{}|]/g, reHasRegExpChar = RegExp(reRegExpChar.source);
      var reTrimStart = /^\s+/;
      var reWhitespace = /\s/;
      var reWrapComment = /\{(?:\n\/\* \[wrapped with .+\] \*\/)?\n?/,
        reWrapDetails = /\{\n\/\* \[wrapped with (.+)\] \*/, reSplitDetails = /,? & /;
      var reAsciiWord = /[^\x00-\x2f\x3a-\x40\x5b-\x60\x7b-\x7f]+/g;
      var reForbiddenIdentifierChars = /[()=,{}\[\]\/\s]/;
      var reEscapeChar = /\\(\\)?/g;
      var reEsTemplate = /\$\{([^\\}]*(?:\\.[^\\}]*)*)\}/g;
      var reFlags = /\w*$/;
      var reIsBadHex = /^[-+]0x[0-9a-f]+$/i;
      var reIsBinary = /^0b[01]+$/i;
      var reIsHostCtor = /^\[object .+?Constructor\]$/;
      var reIsOctal = /^0o[0-7]+$/i;
      var reIsUint = /^(?:0|[1-9]\d*)$/;
      var reLatin = /[\xc0-\xd6\xd8-\xf6\xf8-\xff\u0100-\u017f]/g;
      var reNoMatch = /($^)/;
      var reUnescapedString = /['\n\r\u2028\u2029\\]/g;
      var rsAstralRange = "\\ud800-\\udfff", rsComboMarksRange = "\\u0300-\\u036f",
        reComboHalfMarksRange = "\\ufe20-\\ufe2f", rsComboSymbolsRange = "\\u20d0-\\u20ff",
        rsComboRange = rsComboMarksRange + reComboHalfMarksRange + rsComboSymbolsRange,
        rsDingbatRange = "\\u2700-\\u27bf", rsLowerRange = "a-z\\xdf-\\xf6\\xf8-\\xff",
        rsMathOpRange = "\\xac\\xb1\\xd7\\xf7", rsNonCharRange = "\\x00-\\x2f\\x3a-\\x40\\x5b-\\x60\\x7b-\\xbf",
        rsPunctuationRange = "\\u2000-\\u206f",
        rsSpaceRange = " \\t\\x0b\\f\\xa0\\ufeff\\n\\r\\u2028\\u2029\\u1680\\u180e\\u2000\\u2001\\u2002\\u2003\\u2004\\u2005\\u2006\\u2007\\u2008\\u2009\\u200a\\u202f\\u205f\\u3000",
        rsUpperRange = "A-Z\\xc0-\\xd6\\xd8-\\xde", rsVarRange = "\\ufe0e\\ufe0f",
        rsBreakRange = rsMathOpRange + rsNonCharRange + rsPunctuationRange + rsSpaceRange;
      var rsApos = "['\u2019]", rsAstral = "[" + rsAstralRange + "]", rsBreak = "[" + rsBreakRange + "]",
        rsCombo = "[" + rsComboRange + "]", rsDigits = "\\d+", rsDingbat = "[" + rsDingbatRange + "]",
        rsLower = "[" + rsLowerRange + "]",
        rsMisc = "[^" + rsAstralRange + rsBreakRange + rsDigits + rsDingbatRange + rsLowerRange + rsUpperRange + "]",
        rsFitz = "\\ud83c[\\udffb-\\udfff]", rsModifier = "(?:" + rsCombo + "|" + rsFitz + ")",
        rsNonAstral = "[^" + rsAstralRange + "]", rsRegional = "(?:\\ud83c[\\udde6-\\uddff]){2}",
        rsSurrPair = "[\\ud800-\\udbff][\\udc00-\\udfff]", rsUpper = "[" + rsUpperRange + "]", rsZWJ = "\\u200d";
      var rsMiscLower = "(?:" + rsLower + "|" + rsMisc + ")", rsMiscUpper = "(?:" + rsUpper + "|" + rsMisc + ")",
        rsOptContrLower = "(?:" + rsApos + "(?:d|ll|m|re|s|t|ve))?",
        rsOptContrUpper = "(?:" + rsApos + "(?:D|LL|M|RE|S|T|VE))?", reOptMod = rsModifier + "?",
        rsOptVar = "[" + rsVarRange + "]?",
        rsOptJoin = "(?:" + rsZWJ + "(?:" + [rsNonAstral, rsRegional, rsSurrPair].join("|") + ")" + rsOptVar + reOptMod + ")*",
        rsOrdLower = "\\d*(?:1st|2nd|3rd|(?![123])\\dth)(?=\\b|[A-Z_])",
        rsOrdUpper = "\\d*(?:1ST|2ND|3RD|(?![123])\\dTH)(?=\\b|[a-z_])", rsSeq = rsOptVar + reOptMod + rsOptJoin,
        rsEmoji = "(?:" + [rsDingbat, rsRegional, rsSurrPair].join("|") + ")" + rsSeq,
        rsSymbol = "(?:" + [rsNonAstral + rsCombo + "?", rsCombo, rsRegional, rsSurrPair, rsAstral].join("|") + ")";
      var reApos = RegExp(rsApos, "g");
      var reComboMark = RegExp(rsCombo, "g");
      var reUnicode = RegExp(rsFitz + "(?=" + rsFitz + ")|" + rsSymbol + rsSeq, "g");
      var reUnicodeWord = RegExp([
        rsUpper + "?" + rsLower + "+" + rsOptContrLower + "(?=" + [rsBreak, rsUpper, "$"].join("|") + ")",
        rsMiscUpper + "+" + rsOptContrUpper + "(?=" + [rsBreak, rsUpper + rsMiscLower, "$"].join("|") + ")",
        rsUpper + "?" + rsMiscLower + "+" + rsOptContrLower,
        rsUpper + "+" + rsOptContrUpper,
        rsOrdUpper,
        rsOrdLower,
        rsDigits,
        rsEmoji
      ].join("|"), "g");
      var reHasUnicode = RegExp("[" + rsZWJ + rsAstralRange + rsComboRange + rsVarRange + "]");
      var reHasUnicodeWord = /[a-z][A-Z]|[A-Z]{2}[a-z]|[0-9][a-zA-Z]|[a-zA-Z][0-9]|[^a-zA-Z0-9 ]/;
      var contextProps = [
        "Array",
        "Buffer",
        "DataView",
        "Date",
        "Error",
        "Float32Array",
        "Float64Array",
        "Function",
        "Int8Array",
        "Int16Array",
        "Int32Array",
        "Map",
        "Math",
        "Object",
        "Promise",
        "RegExp",
        "Set",
        "String",
        "Symbol",
        "TypeError",
        "Uint8Array",
        "Uint8ClampedArray",
        "Uint16Array",
        "Uint32Array",
        "WeakMap",
        "_",
        "clearTimeout",
        "isFinite",
        "parseInt",
        "setTimeout"
      ];
      var templateCounter = -1;
      var typedArrayTags = {};
      typedArrayTags[float32Tag] = typedArrayTags[float64Tag] = typedArrayTags[int8Tag] = typedArrayTags[int16Tag] = typedArrayTags[int32Tag] = typedArrayTags[uint8Tag] = typedArrayTags[uint8ClampedTag] = typedArrayTags[uint16Tag] = typedArrayTags[uint32Tag] = true;
      typedArrayTags[argsTag] = typedArrayTags[arrayTag] = typedArrayTags[arrayBufferTag] = typedArrayTags[boolTag] = typedArrayTags[dataViewTag] = typedArrayTags[dateTag] = typedArrayTags[errorTag] = typedArrayTags[funcTag] = typedArrayTags[mapTag] = typedArrayTags[numberTag] = typedArrayTags[objectTag] = typedArrayTags[regexpTag] = typedArrayTags[setTag] = typedArrayTags[stringTag] = typedArrayTags[weakMapTag] = false;
      var cloneableTags = {};
      cloneableTags[argsTag] = cloneableTags[arrayTag] = cloneableTags[arrayBufferTag] = cloneableTags[dataViewTag] = cloneableTags[boolTag] = cloneableTags[dateTag] = cloneableTags[float32Tag] = cloneableTags[float64Tag] = cloneableTags[int8Tag] = cloneableTags[int16Tag] = cloneableTags[int32Tag] = cloneableTags[mapTag] = cloneableTags[numberTag] = cloneableTags[objectTag] = cloneableTags[regexpTag] = cloneableTags[setTag] = cloneableTags[stringTag] = cloneableTags[symbolTag] = cloneableTags[uint8Tag] = cloneableTags[uint8ClampedTag] = cloneableTags[uint16Tag] = cloneableTags[uint32Tag] = true;
      cloneableTags[errorTag] = cloneableTags[funcTag] = cloneableTags[weakMapTag] = false;
      var deburredLetters = {
        "\xC0": "A",
        "\xC1": "A",
        "\xC2": "A",
        "\xC3": "A",
        "\xC4": "A",
        "\xC5": "A",
        "\xE0": "a",
        "\xE1": "a",
        "\xE2": "a",
        "\xE3": "a",
        "\xE4": "a",
        "\xE5": "a",
        "\xC7": "C",
        "\xE7": "c",
        "\xD0": "D",
        "\xF0": "d",
        "\xC8": "E",
        "\xC9": "E",
        "\xCA": "E",
        "\xCB": "E",
        "\xE8": "e",
        "\xE9": "e",
        "\xEA": "e",
        "\xEB": "e",
        "\xCC": "I",
        "\xCD": "I",
        "\xCE": "I",
        "\xCF": "I",
        "\xEC": "i",
        "\xED": "i",
        "\xEE": "i",
        "\xEF": "i",
        "\xD1": "N",
        "\xF1": "n",
        "\xD2": "O",
        "\xD3": "O",
        "\xD4": "O",
        "\xD5": "O",
        "\xD6": "O",
        "\xD8": "O",
        "\xF2": "o",
        "\xF3": "o",
        "\xF4": "o",
        "\xF5": "o",
        "\xF6": "o",
        "\xF8": "o",
        "\xD9": "U",
        "\xDA": "U",
        "\xDB": "U",
        "\xDC": "U",
        "\xF9": "u",
        "\xFA": "u",
        "\xFB": "u",
        "\xFC": "u",
        "\xDD": "Y",
        "\xFD": "y",
        "\xFF": "y",
        "\xC6": "Ae",
        "\xE6": "ae",
        "\xDE": "Th",
        "\xFE": "th",
        "\xDF": "ss",
        "\u0100": "A",
        "\u0102": "A",
        "\u0104": "A",
        "\u0101": "a",
        "\u0103": "a",
        "\u0105": "a",
        "\u0106": "C",
        "\u0108": "C",
        "\u010A": "C",
        "\u010C": "C",
        "\u0107": "c",
        "\u0109": "c",
        "\u010B": "c",
        "\u010D": "c",
        "\u010E": "D",
        "\u0110": "D",
        "\u010F": "d",
        "\u0111": "d",
        "\u0112": "E",
        "\u0114": "E",
        "\u0116": "E",
        "\u0118": "E",
        "\u011A": "E",
        "\u0113": "e",
        "\u0115": "e",
        "\u0117": "e",
        "\u0119": "e",
        "\u011B": "e",
        "\u011C": "G",
        "\u011E": "G",
        "\u0120": "G",
        "\u0122": "G",
        "\u011D": "g",
        "\u011F": "g",
        "\u0121": "g",
        "\u0123": "g",
        "\u0124": "H",
        "\u0126": "H",
        "\u0125": "h",
        "\u0127": "h",
        "\u0128": "I",
        "\u012A": "I",
        "\u012C": "I",
        "\u012E": "I",
        "\u0130": "I",
        "\u0129": "i",
        "\u012B": "i",
        "\u012D": "i",
        "\u012F": "i",
        "\u0131": "i",
        "\u0134": "J",
        "\u0135": "j",
        "\u0136": "K",
        "\u0137": "k",
        "\u0138": "k",
        "\u0139": "L",
        "\u013B": "L",
        "\u013D": "L",
        "\u013F": "L",
        "\u0141": "L",
        "\u013A": "l",
        "\u013C": "l",
        "\u013E": "l",
        "\u0140": "l",
        "\u0142": "l",
        "\u0143": "N",
        "\u0145": "N",
        "\u0147": "N",
        "\u014A": "N",
        "\u0144": "n",
        "\u0146": "n",
        "\u0148": "n",
        "\u014B": "n",
        "\u014C": "O",
        "\u014E": "O",
        "\u0150": "O",
        "\u014D": "o",
        "\u014F": "o",
        "\u0151": "o",
        "\u0154": "R",
        "\u0156": "R",
        "\u0158": "R",
        "\u0155": "r",
        "\u0157": "r",
        "\u0159": "r",
        "\u015A": "S",
        "\u015C": "S",
        "\u015E": "S",
        "\u0160": "S",
        "\u015B": "s",
        "\u015D": "s",
        "\u015F": "s",
        "\u0161": "s",
        "\u0162": "T",
        "\u0164": "T",
        "\u0166": "T",
        "\u0163": "t",
        "\u0165": "t",
        "\u0167": "t",
        "\u0168": "U",
        "\u016A": "U",
        "\u016C": "U",
        "\u016E": "U",
        "\u0170": "U",
        "\u0172": "U",
        "\u0169": "u",
        "\u016B": "u",
        "\u016D": "u",
        "\u016F": "u",
        "\u0171": "u",
        "\u0173": "u",
        "\u0174": "W",
        "\u0175": "w",
        "\u0176": "Y",
        "\u0177": "y",
        "\u0178": "Y",
        "\u0179": "Z",
        "\u017B": "Z",
        "\u017D": "Z",
        "\u017A": "z",
        "\u017C": "z",
        "\u017E": "z",
        "\u0132": "IJ",
        "\u0133": "ij",
        "\u0152": "Oe",
        "\u0153": "oe",
        "\u0149": "'n",
        "\u017F": "s"
      };
      var htmlEscapes = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      };
      var htmlUnescapes = {
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&#39;": "'"
      };
      var stringEscapes = {
        "\\": "\\",
        "'": "'",
        "\n": "n",
        "\r": "r",
        "\u2028": "u2028",
        "\u2029": "u2029"
      };
      var freeParseFloat = parseFloat, freeParseInt = parseInt;
      var freeGlobal = typeof commonjsGlobal == "object" && commonjsGlobal && commonjsGlobal.Object === Object && commonjsGlobal;
      var freeSelf = typeof self == "object" && self && self.Object === Object && self;
      var root = freeGlobal || freeSelf || Function("return this")();
      var freeExports = exports && !exports.nodeType && exports;
      var freeModule = freeExports && true && module && !module.nodeType && module;
      var moduleExports = freeModule && freeModule.exports === freeExports;
      var freeProcess = moduleExports && freeGlobal.process;
      var nodeUtil = function () {
        try {
          var types2 = freeModule && freeModule.require && freeModule.require("util").types;
          if (types2) {
            return types2;
          }
          return freeProcess && freeProcess.binding && freeProcess.binding("util");
        } catch (e) {
        }
      }();
      var nodeIsArrayBuffer = nodeUtil && nodeUtil.isArrayBuffer, nodeIsDate = nodeUtil && nodeUtil.isDate,
        nodeIsMap = nodeUtil && nodeUtil.isMap, nodeIsRegExp = nodeUtil && nodeUtil.isRegExp,
        nodeIsSet = nodeUtil && nodeUtil.isSet, nodeIsTypedArray = nodeUtil && nodeUtil.isTypedArray;

      function apply(func, thisArg, args) {
        switch (args.length) {
          case 0:
            return func.call(thisArg);
          case 1:
            return func.call(thisArg, args[0]);
          case 2:
            return func.call(thisArg, args[0], args[1]);
          case 3:
            return func.call(thisArg, args[0], args[1], args[2]);
        }
        return func.apply(thisArg, args);
      }

      function arrayAggregator(array, setter, iteratee, accumulator) {
        var index = -1, length = array == null ? 0 : array.length;
        while (++index < length) {
          var value = array[index];
          setter(accumulator, value, iteratee(value), array);
        }
        return accumulator;
      }

      function arrayEach(array, iteratee) {
        var index = -1, length = array == null ? 0 : array.length;
        while (++index < length) {
          if (iteratee(array[index], index, array) === false) {
            break;
          }
        }
        return array;
      }

      function arrayEachRight(array, iteratee) {
        var length = array == null ? 0 : array.length;
        while (length--) {
          if (iteratee(array[length], length, array) === false) {
            break;
          }
        }
        return array;
      }

      function arrayEvery(array, predicate) {
        var index = -1, length = array == null ? 0 : array.length;
        while (++index < length) {
          if (!predicate(array[index], index, array)) {
            return false;
          }
        }
        return true;
      }

      function arrayFilter(array, predicate) {
        var index = -1, length = array == null ? 0 : array.length, resIndex = 0, result = [];
        while (++index < length) {
          var value = array[index];
          if (predicate(value, index, array)) {
            result[resIndex++] = value;
          }
        }
        return result;
      }

      function arrayIncludes(array, value) {
        var length = array == null ? 0 : array.length;
        return !!length && baseIndexOf(array, value, 0) > -1;
      }

      function arrayIncludesWith(array, value, comparator) {
        var index = -1, length = array == null ? 0 : array.length;
        while (++index < length) {
          if (comparator(value, array[index])) {
            return true;
          }
        }
        return false;
      }

      function arrayMap(array, iteratee) {
        var index = -1, length = array == null ? 0 : array.length, result = Array(length);
        while (++index < length) {
          result[index] = iteratee(array[index], index, array);
        }
        return result;
      }

      function arrayPush(array, values) {
        var index = -1, length = values.length, offset = array.length;
        while (++index < length) {
          array[offset + index] = values[index];
        }
        return array;
      }

      function arrayReduce(array, iteratee, accumulator, initAccum) {
        var index = -1, length = array == null ? 0 : array.length;
        if (initAccum && length) {
          accumulator = array[++index];
        }
        while (++index < length) {
          accumulator = iteratee(accumulator, array[index], index, array);
        }
        return accumulator;
      }

      function arrayReduceRight(array, iteratee, accumulator, initAccum) {
        var length = array == null ? 0 : array.length;
        if (initAccum && length) {
          accumulator = array[--length];
        }
        while (length--) {
          accumulator = iteratee(accumulator, array[length], length, array);
        }
        return accumulator;
      }

      function arraySome(array, predicate) {
        var index = -1, length = array == null ? 0 : array.length;
        while (++index < length) {
          if (predicate(array[index], index, array)) {
            return true;
          }
        }
        return false;
      }

      var asciiSize = baseProperty("length");

      function asciiToArray(string) {
        return string.split("");
      }

      function asciiWords(string) {
        return string.match(reAsciiWord) || [];
      }

      function baseFindKey(collection, predicate, eachFunc) {
        var result;
        eachFunc(collection, function (value, key, collection2) {
          if (predicate(value, key, collection2)) {
            result = key;
            return false;
          }
        });
        return result;
      }

      function baseFindIndex(array, predicate, fromIndex, fromRight) {
        var length = array.length, index = fromIndex + (fromRight ? 1 : -1);
        while (fromRight ? index-- : ++index < length) {
          if (predicate(array[index], index, array)) {
            return index;
          }
        }
        return -1;
      }

      function baseIndexOf(array, value, fromIndex) {
        return value === value ? strictIndexOf(array, value, fromIndex) : baseFindIndex(array, baseIsNaN, fromIndex);
      }

      function baseIndexOfWith(array, value, fromIndex, comparator) {
        var index = fromIndex - 1, length = array.length;
        while (++index < length) {
          if (comparator(array[index], value)) {
            return index;
          }
        }
        return -1;
      }

      function baseIsNaN(value) {
        return value !== value;
      }

      function baseMean(array, iteratee) {
        var length = array == null ? 0 : array.length;
        return length ? baseSum(array, iteratee) / length : NAN;
      }

      function baseProperty(key) {
        return function (object) {
          return object == null ? undefined$1 : object[key];
        };
      }

      function basePropertyOf(object) {
        return function (key) {
          return object == null ? undefined$1 : object[key];
        };
      }

      function baseReduce(collection, iteratee, accumulator, initAccum, eachFunc) {
        eachFunc(collection, function (value, index, collection2) {
          accumulator = initAccum ? (initAccum = false, value) : iteratee(accumulator, value, index, collection2);
        });
        return accumulator;
      }

      function baseSortBy(array, comparer) {
        var length = array.length;
        array.sort(comparer);
        while (length--) {
          array[length] = array[length].value;
        }
        return array;
      }

      function baseSum(array, iteratee) {
        var result, index = -1, length = array.length;
        while (++index < length) {
          var current = iteratee(array[index]);
          if (current !== undefined$1) {
            result = result === undefined$1 ? current : result + current;
          }
        }
        return result;
      }

      function baseTimes(n, iteratee) {
        var index = -1, result = Array(n);
        while (++index < n) {
          result[index] = iteratee(index);
        }
        return result;
      }

      function baseToPairs(object, props) {
        return arrayMap(props, function (key) {
          return [key, object[key]];
        });
      }

      function baseTrim(string) {
        return string ? string.slice(0, trimmedEndIndex(string) + 1).replace(reTrimStart, "") : string;
      }

      function baseUnary(func) {
        return function (value) {
          return func(value);
        };
      }

      function baseValues(object, props) {
        return arrayMap(props, function (key) {
          return object[key];
        });
      }

      function cacheHas(cache, key) {
        return cache.has(key);
      }

      function charsStartIndex(strSymbols, chrSymbols) {
        var index = -1, length = strSymbols.length;
        while (++index < length && baseIndexOf(chrSymbols, strSymbols[index], 0) > -1) {
        }
        return index;
      }

      function charsEndIndex(strSymbols, chrSymbols) {
        var index = strSymbols.length;
        while (index-- && baseIndexOf(chrSymbols, strSymbols[index], 0) > -1) {
        }
        return index;
      }

      function countHolders(array, placeholder) {
        var length = array.length, result = 0;
        while (length--) {
          if (array[length] === placeholder) {
            ++result;
          }
        }
        return result;
      }

      var deburrLetter = basePropertyOf(deburredLetters);
      var escapeHtmlChar = basePropertyOf(htmlEscapes);

      function escapeStringChar(chr) {
        return "\\" + stringEscapes[chr];
      }

      function getValue(object, key) {
        return object == null ? undefined$1 : object[key];
      }

      function hasUnicode(string) {
        return reHasUnicode.test(string);
      }

      function hasUnicodeWord(string) {
        return reHasUnicodeWord.test(string);
      }

      function iteratorToArray(iterator) {
        var data, result = [];
        while (!(data = iterator.next()).done) {
          result.push(data.value);
        }
        return result;
      }

      function mapToArray(map) {
        var index = -1, result = Array(map.size);
        map.forEach(function (value, key) {
          result[++index] = [key, value];
        });
        return result;
      }

      function overArg(func, transform) {
        return function (arg) {
          return func(transform(arg));
        };
      }

      function replaceHolders(array, placeholder) {
        var index = -1, length = array.length, resIndex = 0, result = [];
        while (++index < length) {
          var value = array[index];
          if (value === placeholder || value === PLACEHOLDER) {
            array[index] = PLACEHOLDER;
            result[resIndex++] = index;
          }
        }
        return result;
      }

      function setToArray(set) {
        var index = -1, result = Array(set.size);
        set.forEach(function (value) {
          result[++index] = value;
        });
        return result;
      }

      function setToPairs(set) {
        var index = -1, result = Array(set.size);
        set.forEach(function (value) {
          result[++index] = [value, value];
        });
        return result;
      }

      function strictIndexOf(array, value, fromIndex) {
        var index = fromIndex - 1, length = array.length;
        while (++index < length) {
          if (array[index] === value) {
            return index;
          }
        }
        return -1;
      }

      function strictLastIndexOf(array, value, fromIndex) {
        var index = fromIndex + 1;
        while (index--) {
          if (array[index] === value) {
            return index;
          }
        }
        return index;
      }

      function stringSize(string) {
        return hasUnicode(string) ? unicodeSize(string) : asciiSize(string);
      }

      function stringToArray(string) {
        return hasUnicode(string) ? unicodeToArray(string) : asciiToArray(string);
      }

      function trimmedEndIndex(string) {
        var index = string.length;
        while (index-- && reWhitespace.test(string.charAt(index))) {
        }
        return index;
      }

      var unescapeHtmlChar = basePropertyOf(htmlUnescapes);

      function unicodeSize(string) {
        var result = reUnicode.lastIndex = 0;
        while (reUnicode.test(string)) {
          ++result;
        }
        return result;
      }

      function unicodeToArray(string) {
        return string.match(reUnicode) || [];
      }

      function unicodeWords(string) {
        return string.match(reUnicodeWord) || [];
      }

      var runInContext = function runInContext2(context) {
        context = context == null ? root : _2.defaults(root.Object(), context, _2.pick(root, contextProps));
        var Array2 = context.Array, Date = context.Date, Error2 = context.Error, Function2 = context.Function,
          Math2 = context.Math, Object2 = context.Object, RegExp2 = context.RegExp, String2 = context.String,
          TypeError2 = context.TypeError;
        var arrayProto = Array2.prototype, funcProto = Function2.prototype, objectProto = Object2.prototype;
        var coreJsData = context["__core-js_shared__"];
        var funcToString = funcProto.toString;
        var hasOwnProperty = objectProto.hasOwnProperty;
        var idCounter = 0;
        var maskSrcKey = function () {
          var uid = /[^.]+$/.exec(coreJsData && coreJsData.keys && coreJsData.keys.IE_PROTO || "");
          return uid ? "Symbol(src)_1." + uid : "";
        }();
        var nativeObjectToString = objectProto.toString;
        var objectCtorString = funcToString.call(Object2);
        var oldDash = root._;
        var reIsNative = RegExp2(
          "^" + funcToString.call(hasOwnProperty).replace(reRegExpChar, "\\$&").replace(/hasOwnProperty|(function).*?(?=\\\()| for .+?(?=\\\])/g, "$1.*?") + "$"
        );
        var Buffer2 = moduleExports ? context.Buffer : undefined$1, Symbol2 = context.Symbol,
          Uint8Array2 = context.Uint8Array, allocUnsafe = Buffer2 ? Buffer2.allocUnsafe : undefined$1,
          getPrototype = overArg(Object2.getPrototypeOf, Object2), objectCreate = Object2.create,
          propertyIsEnumerable = objectProto.propertyIsEnumerable, splice = arrayProto.splice,
          spreadableSymbol = Symbol2 ? Symbol2.isConcatSpreadable : undefined$1,
          symIterator = Symbol2 ? Symbol2.iterator : undefined$1,
          symToStringTag = Symbol2 ? Symbol2.toStringTag : undefined$1;
        var defineProperty2 = function () {
          try {
            var func = getNative(Object2, "defineProperty");
            func({}, "", {});
            return func;
          } catch (e) {
          }
        }();
        var ctxClearTimeout = context.clearTimeout !== root.clearTimeout && context.clearTimeout,
          ctxNow = Date && Date.now !== root.Date.now && Date.now,
          ctxSetTimeout = context.setTimeout !== root.setTimeout && context.setTimeout;
        var nativeCeil = Math2.ceil, nativeFloor = Math2.floor, nativeGetSymbols = Object2.getOwnPropertySymbols,
          nativeIsBuffer = Buffer2 ? Buffer2.isBuffer : undefined$1, nativeIsFinite = context.isFinite,
          nativeJoin = arrayProto.join, nativeKeys = overArg(Object2.keys, Object2), nativeMax = Math2.max,
          nativeMin = Math2.min, nativeNow = Date.now, nativeParseInt = context.parseInt, nativeRandom = Math2.random,
          nativeReverse = arrayProto.reverse;
        var DataView = getNative(context, "DataView"), Map2 = getNative(context, "Map"),
          Promise2 = getNative(context, "Promise"), Set2 = getNative(context, "Set"),
          WeakMap2 = getNative(context, "WeakMap"), nativeCreate = getNative(Object2, "create");
        var metaMap = WeakMap2 && new WeakMap2();
        var realNames = {};
        var dataViewCtorString = toSource(DataView), mapCtorString = toSource(Map2),
          promiseCtorString = toSource(Promise2), setCtorString = toSource(Set2),
          weakMapCtorString = toSource(WeakMap2);
        var symbolProto = Symbol2 ? Symbol2.prototype : undefined$1,
          symbolValueOf = symbolProto ? symbolProto.valueOf : undefined$1,
          symbolToString = symbolProto ? symbolProto.toString : undefined$1;

        function lodash2(value) {
          if (isObjectLike(value) && !isArray(value) && !(value instanceof LazyWrapper)) {
            if (value instanceof LodashWrapper) {
              return value;
            }
            if (hasOwnProperty.call(value, "__wrapped__")) {
              return wrapperClone(value);
            }
          }
          return new LodashWrapper(value);
        }

        var baseCreate = function () {
          function object() {
          }

          return function (proto) {
            if (!isObject(proto)) {
              return {};
            }
            if (objectCreate) {
              return objectCreate(proto);
            }
            object.prototype = proto;
            var result2 = new object();
            object.prototype = undefined$1;
            return result2;
          };
        }();

        function baseLodash() {
        }

        function LodashWrapper(value, chainAll) {
          this.__wrapped__ = value;
          this.__actions__ = [];
          this.__chain__ = !!chainAll;
          this.__index__ = 0;
          this.__values__ = undefined$1;
        }

        lodash2.templateSettings = {
          "escape": reEscape,
          "evaluate": reEvaluate,
          "interpolate": reInterpolate,
          "variable": "",
          "imports": {
            "_": lodash2
          }
        };
        lodash2.prototype = baseLodash.prototype;
        lodash2.prototype.constructor = lodash2;
        LodashWrapper.prototype = baseCreate(baseLodash.prototype);
        LodashWrapper.prototype.constructor = LodashWrapper;

        function LazyWrapper(value) {
          this.__wrapped__ = value;
          this.__actions__ = [];
          this.__dir__ = 1;
          this.__filtered__ = false;
          this.__iteratees__ = [];
          this.__takeCount__ = MAX_ARRAY_LENGTH;
          this.__views__ = [];
        }

        function lazyClone() {
          var result2 = new LazyWrapper(this.__wrapped__);
          result2.__actions__ = copyArray(this.__actions__);
          result2.__dir__ = this.__dir__;
          result2.__filtered__ = this.__filtered__;
          result2.__iteratees__ = copyArray(this.__iteratees__);
          result2.__takeCount__ = this.__takeCount__;
          result2.__views__ = copyArray(this.__views__);
          return result2;
        }

        function lazyReverse() {
          if (this.__filtered__) {
            var result2 = new LazyWrapper(this);
            result2.__dir__ = -1;
            result2.__filtered__ = true;
          } else {
            result2 = this.clone();
            result2.__dir__ *= -1;
          }
          return result2;
        }

        function lazyValue() {
          var array = this.__wrapped__.value(), dir = this.__dir__, isArr = isArray(array), isRight = dir < 0,
            arrLength = isArr ? array.length : 0, view = getView(0, arrLength, this.__views__), start = view.start,
            end = view.end, length = end - start, index = isRight ? end : start - 1, iteratees = this.__iteratees__,
            iterLength = iteratees.length, resIndex = 0, takeCount = nativeMin(length, this.__takeCount__);
          if (!isArr || !isRight && arrLength == length && takeCount == length) {
            return baseWrapperValue(array, this.__actions__);
          }
          var result2 = [];
          outer:
            while (length-- && resIndex < takeCount) {
              index += dir;
              var iterIndex = -1, value = array[index];
              while (++iterIndex < iterLength) {
                var data = iteratees[iterIndex], iteratee2 = data.iteratee, type = data.type,
                  computed = iteratee2(value);
                if (type == LAZY_MAP_FLAG) {
                  value = computed;
                } else if (!computed) {
                  if (type == LAZY_FILTER_FLAG) {
                    continue outer;
                  } else {
                    break outer;
                  }
                }
              }
              result2[resIndex++] = value;
            }
          return result2;
        }

        LazyWrapper.prototype = baseCreate(baseLodash.prototype);
        LazyWrapper.prototype.constructor = LazyWrapper;

        function Hash(entries) {
          var index = -1, length = entries == null ? 0 : entries.length;
          this.clear();
          while (++index < length) {
            var entry = entries[index];
            this.set(entry[0], entry[1]);
          }
        }

        function hashClear() {
          this.__data__ = nativeCreate ? nativeCreate(null) : {};
          this.size = 0;
        }

        function hashDelete(key) {
          var result2 = this.has(key) && delete this.__data__[key];
          this.size -= result2 ? 1 : 0;
          return result2;
        }

        function hashGet(key) {
          var data = this.__data__;
          if (nativeCreate) {
            var result2 = data[key];
            return result2 === HASH_UNDEFINED ? undefined$1 : result2;
          }
          return hasOwnProperty.call(data, key) ? data[key] : undefined$1;
        }

        function hashHas(key) {
          var data = this.__data__;
          return nativeCreate ? data[key] !== undefined$1 : hasOwnProperty.call(data, key);
        }

        function hashSet(key, value) {
          var data = this.__data__;
          this.size += this.has(key) ? 0 : 1;
          data[key] = nativeCreate && value === undefined$1 ? HASH_UNDEFINED : value;
          return this;
        }

        Hash.prototype.clear = hashClear;
        Hash.prototype["delete"] = hashDelete;
        Hash.prototype.get = hashGet;
        Hash.prototype.has = hashHas;
        Hash.prototype.set = hashSet;

        function ListCache(entries) {
          var index = -1, length = entries == null ? 0 : entries.length;
          this.clear();
          while (++index < length) {
            var entry = entries[index];
            this.set(entry[0], entry[1]);
          }
        }

        function listCacheClear() {
          this.__data__ = [];
          this.size = 0;
        }

        function listCacheDelete(key) {
          var data = this.__data__, index = assocIndexOf(data, key);
          if (index < 0) {
            return false;
          }
          var lastIndex = data.length - 1;
          if (index == lastIndex) {
            data.pop();
          } else {
            splice.call(data, index, 1);
          }
          --this.size;
          return true;
        }

        function listCacheGet(key) {
          var data = this.__data__, index = assocIndexOf(data, key);
          return index < 0 ? undefined$1 : data[index][1];
        }

        function listCacheHas(key) {
          return assocIndexOf(this.__data__, key) > -1;
        }

        function listCacheSet(key, value) {
          var data = this.__data__, index = assocIndexOf(data, key);
          if (index < 0) {
            ++this.size;
            data.push([key, value]);
          } else {
            data[index][1] = value;
          }
          return this;
        }

        ListCache.prototype.clear = listCacheClear;
        ListCache.prototype["delete"] = listCacheDelete;
        ListCache.prototype.get = listCacheGet;
        ListCache.prototype.has = listCacheHas;
        ListCache.prototype.set = listCacheSet;

        function MapCache(entries) {
          var index = -1, length = entries == null ? 0 : entries.length;
          this.clear();
          while (++index < length) {
            var entry = entries[index];
            this.set(entry[0], entry[1]);
          }
        }

        function mapCacheClear() {
          this.size = 0;
          this.__data__ = {
            "hash": new Hash(),
            "map": new (Map2 || ListCache)(),
            "string": new Hash()
          };
        }

        function mapCacheDelete(key) {
          var result2 = getMapData(this, key)["delete"](key);
          this.size -= result2 ? 1 : 0;
          return result2;
        }

        function mapCacheGet(key) {
          return getMapData(this, key).get(key);
        }

        function mapCacheHas(key) {
          return getMapData(this, key).has(key);
        }

        function mapCacheSet(key, value) {
          var data = getMapData(this, key), size2 = data.size;
          data.set(key, value);
          this.size += data.size == size2 ? 0 : 1;
          return this;
        }

        MapCache.prototype.clear = mapCacheClear;
        MapCache.prototype["delete"] = mapCacheDelete;
        MapCache.prototype.get = mapCacheGet;
        MapCache.prototype.has = mapCacheHas;
        MapCache.prototype.set = mapCacheSet;

        function SetCache(values2) {
          var index = -1, length = values2 == null ? 0 : values2.length;
          this.__data__ = new MapCache();
          while (++index < length) {
            this.add(values2[index]);
          }
        }

        function setCacheAdd(value) {
          this.__data__.set(value, HASH_UNDEFINED);
          return this;
        }

        function setCacheHas(value) {
          return this.__data__.has(value);
        }

        SetCache.prototype.add = SetCache.prototype.push = setCacheAdd;
        SetCache.prototype.has = setCacheHas;

        function Stack(entries) {
          var data = this.__data__ = new ListCache(entries);
          this.size = data.size;
        }

        function stackClear() {
          this.__data__ = new ListCache();
          this.size = 0;
        }

        function stackDelete(key) {
          var data = this.__data__, result2 = data["delete"](key);
          this.size = data.size;
          return result2;
        }

        function stackGet(key) {
          return this.__data__.get(key);
        }

        function stackHas(key) {
          return this.__data__.has(key);
        }

        function stackSet(key, value) {
          var data = this.__data__;
          if (data instanceof ListCache) {
            var pairs = data.__data__;
            if (!Map2 || pairs.length < LARGE_ARRAY_SIZE - 1) {
              pairs.push([key, value]);
              this.size = ++data.size;
              return this;
            }
            data = this.__data__ = new MapCache(pairs);
          }
          data.set(key, value);
          this.size = data.size;
          return this;
        }

        Stack.prototype.clear = stackClear;
        Stack.prototype["delete"] = stackDelete;
        Stack.prototype.get = stackGet;
        Stack.prototype.has = stackHas;
        Stack.prototype.set = stackSet;

        function arrayLikeKeys(value, inherited) {
          var isArr = isArray(value), isArg = !isArr && isArguments(value),
            isBuff = !isArr && !isArg && isBuffer(value), isType = !isArr && !isArg && !isBuff && isTypedArray(value),
            skipIndexes = isArr || isArg || isBuff || isType,
            result2 = skipIndexes ? baseTimes(value.length, String2) : [], length = result2.length;
          for (var key in value) {
            if ((inherited || hasOwnProperty.call(value, key)) && !(skipIndexes && (key == "length" || isBuff && (key == "offset" || key == "parent") || isType && (key == "buffer" || key == "byteLength" || key == "byteOffset") || isIndex(key, length)))) {
              result2.push(key);
            }
          }
          return result2;
        }

        function arraySample(array) {
          var length = array.length;
          return length ? array[baseRandom(0, length - 1)] : undefined$1;
        }

        function arraySampleSize(array, n) {
          return shuffleSelf(copyArray(array), baseClamp(n, 0, array.length));
        }

        function arrayShuffle(array) {
          return shuffleSelf(copyArray(array));
        }

        function assignMergeValue(object, key, value) {
          if (value !== undefined$1 && !eq(object[key], value) || value === undefined$1 && !(key in object)) {
            baseAssignValue(object, key, value);
          }
        }

        function assignValue(object, key, value) {
          var objValue = object[key];
          if (!(hasOwnProperty.call(object, key) && eq(objValue, value)) || value === undefined$1 && !(key in object)) {
            baseAssignValue(object, key, value);
          }
        }

        function assocIndexOf(array, key) {
          var length = array.length;
          while (length--) {
            if (eq(array[length][0], key)) {
              return length;
            }
          }
          return -1;
        }

        function baseAggregator(collection, setter, iteratee2, accumulator) {
          baseEach(collection, function (value, key, collection2) {
            setter(accumulator, value, iteratee2(value), collection2);
          });
          return accumulator;
        }

        function baseAssign(object, source) {
          return object && copyObject(source, keys(source), object);
        }

        function baseAssignIn(object, source) {
          return object && copyObject(source, keysIn(source), object);
        }

        function baseAssignValue(object, key, value) {
          if (key == "__proto__" && defineProperty2) {
            defineProperty2(object, key, {
              "configurable": true,
              "enumerable": true,
              "value": value,
              "writable": true
            });
          } else {
            object[key] = value;
          }
        }

        function baseAt(object, paths) {
          var index = -1, length = paths.length, result2 = Array2(length), skip = object == null;
          while (++index < length) {
            result2[index] = skip ? undefined$1 : get(object, paths[index]);
          }
          return result2;
        }

        function baseClamp(number, lower, upper) {
          if (number === number) {
            if (upper !== undefined$1) {
              number = number <= upper ? number : upper;
            }
            if (lower !== undefined$1) {
              number = number >= lower ? number : lower;
            }
          }
          return number;
        }

        function baseClone(value, bitmask, customizer, key, object, stack) {
          var result2, isDeep = bitmask & CLONE_DEEP_FLAG, isFlat = bitmask & CLONE_FLAT_FLAG,
            isFull = bitmask & CLONE_SYMBOLS_FLAG;
          if (customizer) {
            result2 = object ? customizer(value, key, object, stack) : customizer(value);
          }
          if (result2 !== undefined$1) {
            return result2;
          }
          if (!isObject(value)) {
            return value;
          }
          var isArr = isArray(value);
          if (isArr) {
            result2 = initCloneArray(value);
            if (!isDeep) {
              return copyArray(value, result2);
            }
          } else {
            var tag = getTag(value), isFunc = tag == funcTag || tag == genTag;
            if (isBuffer(value)) {
              return cloneBuffer(value, isDeep);
            }
            if (tag == objectTag || tag == argsTag || isFunc && !object) {
              result2 = isFlat || isFunc ? {} : initCloneObject(value);
              if (!isDeep) {
                return isFlat ? copySymbolsIn(value, baseAssignIn(result2, value)) : copySymbols(value, baseAssign(result2, value));
              }
            } else {
              if (!cloneableTags[tag]) {
                return object ? value : {};
              }
              result2 = initCloneByTag(value, tag, isDeep);
            }
          }
          stack || (stack = new Stack());
          var stacked = stack.get(value);
          if (stacked) {
            return stacked;
          }
          stack.set(value, result2);
          if (isSet(value)) {
            value.forEach(function (subValue) {
              result2.add(baseClone(subValue, bitmask, customizer, subValue, value, stack));
            });
          } else if (isMap(value)) {
            value.forEach(function (subValue, key2) {
              result2.set(key2, baseClone(subValue, bitmask, customizer, key2, value, stack));
            });
          }
          var keysFunc = isFull ? isFlat ? getAllKeysIn : getAllKeys : isFlat ? keysIn : keys;
          var props = isArr ? undefined$1 : keysFunc(value);
          arrayEach(props || value, function (subValue, key2) {
            if (props) {
              key2 = subValue;
              subValue = value[key2];
            }
            assignValue(result2, key2, baseClone(subValue, bitmask, customizer, key2, value, stack));
          });
          return result2;
        }

        function baseConforms(source) {
          var props = keys(source);
          return function (object) {
            return baseConformsTo(object, source, props);
          };
        }

        function baseConformsTo(object, source, props) {
          var length = props.length;
          if (object == null) {
            return !length;
          }
          object = Object2(object);
          while (length--) {
            var key = props[length], predicate = source[key], value = object[key];
            if (value === undefined$1 && !(key in object) || !predicate(value)) {
              return false;
            }
          }
          return true;
        }

        function baseDelay(func, wait, args) {
          if (typeof func != "function") {
            throw new TypeError2(FUNC_ERROR_TEXT);
          }
          return setTimeout(function () {
            func.apply(undefined$1, args);
          }, wait);
        }

        function baseDifference(array, values2, iteratee2, comparator) {
          var index = -1, includes2 = arrayIncludes, isCommon = true, length = array.length, result2 = [],
            valuesLength = values2.length;
          if (!length) {
            return result2;
          }
          if (iteratee2) {
            values2 = arrayMap(values2, baseUnary(iteratee2));
          }
          if (comparator) {
            includes2 = arrayIncludesWith;
            isCommon = false;
          } else if (values2.length >= LARGE_ARRAY_SIZE) {
            includes2 = cacheHas;
            isCommon = false;
            values2 = new SetCache(values2);
          }
          outer:
            while (++index < length) {
              var value = array[index], computed = iteratee2 == null ? value : iteratee2(value);
              value = comparator || value !== 0 ? value : 0;
              if (isCommon && computed === computed) {
                var valuesIndex = valuesLength;
                while (valuesIndex--) {
                  if (values2[valuesIndex] === computed) {
                    continue outer;
                  }
                }
                result2.push(value);
              } else if (!includes2(values2, computed, comparator)) {
                result2.push(value);
              }
            }
          return result2;
        }

        var baseEach = createBaseEach(baseForOwn);
        var baseEachRight = createBaseEach(baseForOwnRight, true);

        function baseEvery(collection, predicate) {
          var result2 = true;
          baseEach(collection, function (value, index, collection2) {
            result2 = !!predicate(value, index, collection2);
            return result2;
          });
          return result2;
        }

        function baseExtremum(array, iteratee2, comparator) {
          var index = -1, length = array.length;
          while (++index < length) {
            var value = array[index], current = iteratee2(value);
            if (current != null && (computed === undefined$1 ? current === current && !isSymbol(current) : comparator(current, computed))) {
              var computed = current, result2 = value;
            }
          }
          return result2;
        }

        function baseFill(array, value, start, end) {
          var length = array.length;
          start = toInteger(start);
          if (start < 0) {
            start = -start > length ? 0 : length + start;
          }
          end = end === undefined$1 || end > length ? length : toInteger(end);
          if (end < 0) {
            end += length;
          }
          end = start > end ? 0 : toLength(end);
          while (start < end) {
            array[start++] = value;
          }
          return array;
        }

        function baseFilter(collection, predicate) {
          var result2 = [];
          baseEach(collection, function (value, index, collection2) {
            if (predicate(value, index, collection2)) {
              result2.push(value);
            }
          });
          return result2;
        }

        function baseFlatten(array, depth, predicate, isStrict, result2) {
          var index = -1, length = array.length;
          predicate || (predicate = isFlattenable);
          result2 || (result2 = []);
          while (++index < length) {
            var value = array[index];
            if (depth > 0 && predicate(value)) {
              if (depth > 1) {
                baseFlatten(value, depth - 1, predicate, isStrict, result2);
              } else {
                arrayPush(result2, value);
              }
            } else if (!isStrict) {
              result2[result2.length] = value;
            }
          }
          return result2;
        }

        var baseFor = createBaseFor();
        var baseForRight = createBaseFor(true);

        function baseForOwn(object, iteratee2) {
          return object && baseFor(object, iteratee2, keys);
        }

        function baseForOwnRight(object, iteratee2) {
          return object && baseForRight(object, iteratee2, keys);
        }

        function baseFunctions(object, props) {
          return arrayFilter(props, function (key) {
            return isFunction(object[key]);
          });
        }

        function baseGet(object, path) {
          path = castPath(path, object);
          var index = 0, length = path.length;
          while (object != null && index < length) {
            object = object[toKey(path[index++])];
          }
          return index && index == length ? object : undefined$1;
        }

        function baseGetAllKeys(object, keysFunc, symbolsFunc) {
          var result2 = keysFunc(object);
          return isArray(object) ? result2 : arrayPush(result2, symbolsFunc(object));
        }

        function baseGetTag(value) {
          if (value == null) {
            return value === undefined$1 ? undefinedTag : nullTag;
          }
          return symToStringTag && symToStringTag in Object2(value) ? getRawTag(value) : objectToString(value);
        }

        function baseGt(value, other) {
          return value > other;
        }

        function baseHas(object, key) {
          return object != null && hasOwnProperty.call(object, key);
        }

        function baseHasIn(object, key) {
          return object != null && key in Object2(object);
        }

        function baseInRange(number, start, end) {
          return number >= nativeMin(start, end) && number < nativeMax(start, end);
        }

        function baseIntersection(arrays, iteratee2, comparator) {
          var includes2 = comparator ? arrayIncludesWith : arrayIncludes, length = arrays[0].length,
            othLength = arrays.length, othIndex = othLength, caches = Array2(othLength), maxLength = Infinity,
            result2 = [];
          while (othIndex--) {
            var array = arrays[othIndex];
            if (othIndex && iteratee2) {
              array = arrayMap(array, baseUnary(iteratee2));
            }
            maxLength = nativeMin(array.length, maxLength);
            caches[othIndex] = !comparator && (iteratee2 || length >= 120 && array.length >= 120) ? new SetCache(othIndex && array) : undefined$1;
          }
          array = arrays[0];
          var index = -1, seen = caches[0];
          outer:
            while (++index < length && result2.length < maxLength) {
              var value = array[index], computed = iteratee2 ? iteratee2(value) : value;
              value = comparator || value !== 0 ? value : 0;
              if (!(seen ? cacheHas(seen, computed) : includes2(result2, computed, comparator))) {
                othIndex = othLength;
                while (--othIndex) {
                  var cache = caches[othIndex];
                  if (!(cache ? cacheHas(cache, computed) : includes2(arrays[othIndex], computed, comparator))) {
                    continue outer;
                  }
                }
                if (seen) {
                  seen.push(computed);
                }
                result2.push(value);
              }
            }
          return result2;
        }

        function baseInverter(object, setter, iteratee2, accumulator) {
          baseForOwn(object, function (value, key, object2) {
            setter(accumulator, iteratee2(value), key, object2);
          });
          return accumulator;
        }

        function baseInvoke(object, path, args) {
          path = castPath(path, object);
          object = parent(object, path);
          var func = object == null ? object : object[toKey(last(path))];
          return func == null ? undefined$1 : apply(func, object, args);
        }

        function baseIsArguments(value) {
          return isObjectLike(value) && baseGetTag(value) == argsTag;
        }

        function baseIsArrayBuffer(value) {
          return isObjectLike(value) && baseGetTag(value) == arrayBufferTag;
        }

        function baseIsDate(value) {
          return isObjectLike(value) && baseGetTag(value) == dateTag;
        }

        function baseIsEqual(value, other, bitmask, customizer, stack) {
          if (value === other) {
            return true;
          }
          if (value == null || other == null || !isObjectLike(value) && !isObjectLike(other)) {
            return value !== value && other !== other;
          }
          return baseIsEqualDeep(value, other, bitmask, customizer, baseIsEqual, stack);
        }

        function baseIsEqualDeep(object, other, bitmask, customizer, equalFunc, stack) {
          var objIsArr = isArray(object), othIsArr = isArray(other), objTag = objIsArr ? arrayTag : getTag(object),
            othTag = othIsArr ? arrayTag : getTag(other);
          objTag = objTag == argsTag ? objectTag : objTag;
          othTag = othTag == argsTag ? objectTag : othTag;
          var objIsObj = objTag == objectTag, othIsObj = othTag == objectTag, isSameTag = objTag == othTag;
          if (isSameTag && isBuffer(object)) {
            if (!isBuffer(other)) {
              return false;
            }
            objIsArr = true;
            objIsObj = false;
          }
          if (isSameTag && !objIsObj) {
            stack || (stack = new Stack());
            return objIsArr || isTypedArray(object) ? equalArrays(object, other, bitmask, customizer, equalFunc, stack) : equalByTag(object, other, objTag, bitmask, customizer, equalFunc, stack);
          }
          if (!(bitmask & COMPARE_PARTIAL_FLAG)) {
            var objIsWrapped = objIsObj && hasOwnProperty.call(object, "__wrapped__"),
              othIsWrapped = othIsObj && hasOwnProperty.call(other, "__wrapped__");
            if (objIsWrapped || othIsWrapped) {
              var objUnwrapped = objIsWrapped ? object.value() : object,
                othUnwrapped = othIsWrapped ? other.value() : other;
              stack || (stack = new Stack());
              return equalFunc(objUnwrapped, othUnwrapped, bitmask, customizer, stack);
            }
          }
          if (!isSameTag) {
            return false;
          }
          stack || (stack = new Stack());
          return equalObjects(object, other, bitmask, customizer, equalFunc, stack);
        }

        function baseIsMap(value) {
          return isObjectLike(value) && getTag(value) == mapTag;
        }

        function baseIsMatch(object, source, matchData, customizer) {
          var index = matchData.length, length = index, noCustomizer = !customizer;
          if (object == null) {
            return !length;
          }
          object = Object2(object);
          while (index--) {
            var data = matchData[index];
            if (noCustomizer && data[2] ? data[1] !== object[data[0]] : !(data[0] in object)) {
              return false;
            }
          }
          while (++index < length) {
            data = matchData[index];
            var key = data[0], objValue = object[key], srcValue = data[1];
            if (noCustomizer && data[2]) {
              if (objValue === undefined$1 && !(key in object)) {
                return false;
              }
            } else {
              var stack = new Stack();
              if (customizer) {
                var result2 = customizer(objValue, srcValue, key, object, source, stack);
              }
              if (!(result2 === undefined$1 ? baseIsEqual(srcValue, objValue, COMPARE_PARTIAL_FLAG | COMPARE_UNORDERED_FLAG, customizer, stack) : result2)) {
                return false;
              }
            }
          }
          return true;
        }

        function baseIsNative(value) {
          if (!isObject(value) || isMasked(value)) {
            return false;
          }
          var pattern = isFunction(value) ? reIsNative : reIsHostCtor;
          return pattern.test(toSource(value));
        }

        function baseIsRegExp(value) {
          return isObjectLike(value) && baseGetTag(value) == regexpTag;
        }

        function baseIsSet(value) {
          return isObjectLike(value) && getTag(value) == setTag;
        }

        function baseIsTypedArray(value) {
          return isObjectLike(value) && isLength(value.length) && !!typedArrayTags[baseGetTag(value)];
        }

        function baseIteratee(value) {
          if (typeof value == "function") {
            return value;
          }
          if (value == null) {
            return identity;
          }
          if (typeof value == "object") {
            return isArray(value) ? baseMatchesProperty(value[0], value[1]) : baseMatches(value);
          }
          return property(value);
        }

        function baseKeys(object) {
          if (!isPrototype(object)) {
            return nativeKeys(object);
          }
          var result2 = [];
          for (var key in Object2(object)) {
            if (hasOwnProperty.call(object, key) && key != "constructor") {
              result2.push(key);
            }
          }
          return result2;
        }

        function baseKeysIn(object) {
          if (!isObject(object)) {
            return nativeKeysIn(object);
          }
          var isProto = isPrototype(object), result2 = [];
          for (var key in object) {
            if (!(key == "constructor" && (isProto || !hasOwnProperty.call(object, key)))) {
              result2.push(key);
            }
          }
          return result2;
        }

        function baseLt(value, other) {
          return value < other;
        }

        function baseMap(collection, iteratee2) {
          var index = -1, result2 = isArrayLike(collection) ? Array2(collection.length) : [];
          baseEach(collection, function (value, key, collection2) {
            result2[++index] = iteratee2(value, key, collection2);
          });
          return result2;
        }

        function baseMatches(source) {
          var matchData = getMatchData(source);
          if (matchData.length == 1 && matchData[0][2]) {
            return matchesStrictComparable(matchData[0][0], matchData[0][1]);
          }
          return function (object) {
            return object === source || baseIsMatch(object, source, matchData);
          };
        }

        function baseMatchesProperty(path, srcValue) {
          if (isKey(path) && isStrictComparable(srcValue)) {
            return matchesStrictComparable(toKey(path), srcValue);
          }
          return function (object) {
            var objValue = get(object, path);
            return objValue === undefined$1 && objValue === srcValue ? hasIn(object, path) : baseIsEqual(srcValue, objValue, COMPARE_PARTIAL_FLAG | COMPARE_UNORDERED_FLAG);
          };
        }

        function baseMerge(object, source, srcIndex, customizer, stack) {
          if (object === source) {
            return;
          }
          baseFor(source, function (srcValue, key) {
            stack || (stack = new Stack());
            if (isObject(srcValue)) {
              baseMergeDeep(object, source, key, srcIndex, baseMerge, customizer, stack);
            } else {
              var newValue = customizer ? customizer(safeGet(object, key), srcValue, key + "", object, source, stack) : undefined$1;
              if (newValue === undefined$1) {
                newValue = srcValue;
              }
              assignMergeValue(object, key, newValue);
            }
          }, keysIn);
        }

        function baseMergeDeep(object, source, key, srcIndex, mergeFunc, customizer, stack) {
          var objValue = safeGet(object, key), srcValue = safeGet(source, key), stacked = stack.get(srcValue);
          if (stacked) {
            assignMergeValue(object, key, stacked);
            return;
          }
          var newValue = customizer ? customizer(objValue, srcValue, key + "", object, source, stack) : undefined$1;
          var isCommon = newValue === undefined$1;
          if (isCommon) {
            var isArr = isArray(srcValue), isBuff = !isArr && isBuffer(srcValue),
              isTyped = !isArr && !isBuff && isTypedArray(srcValue);
            newValue = srcValue;
            if (isArr || isBuff || isTyped) {
              if (isArray(objValue)) {
                newValue = objValue;
              } else if (isArrayLikeObject(objValue)) {
                newValue = copyArray(objValue);
              } else if (isBuff) {
                isCommon = false;
                newValue = cloneBuffer(srcValue, true);
              } else if (isTyped) {
                isCommon = false;
                newValue = cloneTypedArray(srcValue, true);
              } else {
                newValue = [];
              }
            } else if (isPlainObject(srcValue) || isArguments(srcValue)) {
              newValue = objValue;
              if (isArguments(objValue)) {
                newValue = toPlainObject(objValue);
              } else if (!isObject(objValue) || isFunction(objValue)) {
                newValue = initCloneObject(srcValue);
              }
            } else {
              isCommon = false;
            }
          }
          if (isCommon) {
            stack.set(srcValue, newValue);
            mergeFunc(newValue, srcValue, srcIndex, customizer, stack);
            stack["delete"](srcValue);
          }
          assignMergeValue(object, key, newValue);
        }

        function baseNth(array, n) {
          var length = array.length;
          if (!length) {
            return;
          }
          n += n < 0 ? length : 0;
          return isIndex(n, length) ? array[n] : undefined$1;
        }

        function baseOrderBy(collection, iteratees, orders) {
          if (iteratees.length) {
            iteratees = arrayMap(iteratees, function (iteratee2) {
              if (isArray(iteratee2)) {
                return function (value) {
                  return baseGet(value, iteratee2.length === 1 ? iteratee2[0] : iteratee2);
                };
              }
              return iteratee2;
            });
          } else {
            iteratees = [identity];
          }
          var index = -1;
          iteratees = arrayMap(iteratees, baseUnary(getIteratee()));
          var result2 = baseMap(collection, function (value, key, collection2) {
            var criteria = arrayMap(iteratees, function (iteratee2) {
              return iteratee2(value);
            });
            return {"criteria": criteria, "index": ++index, "value": value};
          });
          return baseSortBy(result2, function (object, other) {
            return compareMultiple(object, other, orders);
          });
        }

        function basePick(object, paths) {
          return basePickBy(object, paths, function (value, path) {
            return hasIn(object, path);
          });
        }

        function basePickBy(object, paths, predicate) {
          var index = -1, length = paths.length, result2 = {};
          while (++index < length) {
            var path = paths[index], value = baseGet(object, path);
            if (predicate(value, path)) {
              baseSet(result2, castPath(path, object), value);
            }
          }
          return result2;
        }

        function basePropertyDeep(path) {
          return function (object) {
            return baseGet(object, path);
          };
        }

        function basePullAll(array, values2, iteratee2, comparator) {
          var indexOf2 = comparator ? baseIndexOfWith : baseIndexOf, index = -1, length = values2.length, seen = array;
          if (array === values2) {
            values2 = copyArray(values2);
          }
          if (iteratee2) {
            seen = arrayMap(array, baseUnary(iteratee2));
          }
          while (++index < length) {
            var fromIndex = 0, value = values2[index], computed = iteratee2 ? iteratee2(value) : value;
            while ((fromIndex = indexOf2(seen, computed, fromIndex, comparator)) > -1) {
              if (seen !== array) {
                splice.call(seen, fromIndex, 1);
              }
              splice.call(array, fromIndex, 1);
            }
          }
          return array;
        }

        function basePullAt(array, indexes) {
          var length = array ? indexes.length : 0, lastIndex = length - 1;
          while (length--) {
            var index = indexes[length];
            if (length == lastIndex || index !== previous) {
              var previous = index;
              if (isIndex(index)) {
                splice.call(array, index, 1);
              } else {
                baseUnset(array, index);
              }
            }
          }
          return array;
        }

        function baseRandom(lower, upper) {
          return lower + nativeFloor(nativeRandom() * (upper - lower + 1));
        }

        function baseRange(start, end, step, fromRight) {
          var index = -1, length = nativeMax(nativeCeil((end - start) / (step || 1)), 0), result2 = Array2(length);
          while (length--) {
            result2[fromRight ? length : ++index] = start;
            start += step;
          }
          return result2;
        }

        function baseRepeat(string, n) {
          var result2 = "";
          if (!string || n < 1 || n > MAX_SAFE_INTEGER) {
            return result2;
          }
          do {
            if (n % 2) {
              result2 += string;
            }
            n = nativeFloor(n / 2);
            if (n) {
              string += string;
            }
          } while (n);
          return result2;
        }

        function baseRest(func, start) {
          return setToString(overRest(func, start, identity), func + "");
        }

        function baseSample(collection) {
          return arraySample(values(collection));
        }

        function baseSampleSize(collection, n) {
          var array = values(collection);
          return shuffleSelf(array, baseClamp(n, 0, array.length));
        }

        function baseSet(object, path, value, customizer) {
          if (!isObject(object)) {
            return object;
          }
          path = castPath(path, object);
          var index = -1, length = path.length, lastIndex = length - 1, nested = object;
          while (nested != null && ++index < length) {
            var key = toKey(path[index]), newValue = value;
            if (key === "__proto__" || key === "constructor" || key === "prototype") {
              return object;
            }
            if (index != lastIndex) {
              var objValue = nested[key];
              newValue = customizer ? customizer(objValue, key, nested) : undefined$1;
              if (newValue === undefined$1) {
                newValue = isObject(objValue) ? objValue : isIndex(path[index + 1]) ? [] : {};
              }
            }
            assignValue(nested, key, newValue);
            nested = nested[key];
          }
          return object;
        }

        var baseSetData = !metaMap ? identity : function (func, data) {
          metaMap.set(func, data);
          return func;
        };
        var baseSetToString = !defineProperty2 ? identity : function (func, string) {
          return defineProperty2(func, "toString", {
            "configurable": true,
            "enumerable": false,
            "value": constant(string),
            "writable": true
          });
        };

        function baseShuffle(collection) {
          return shuffleSelf(values(collection));
        }

        function baseSlice(array, start, end) {
          var index = -1, length = array.length;
          if (start < 0) {
            start = -start > length ? 0 : length + start;
          }
          end = end > length ? length : end;
          if (end < 0) {
            end += length;
          }
          length = start > end ? 0 : end - start >>> 0;
          start >>>= 0;
          var result2 = Array2(length);
          while (++index < length) {
            result2[index] = array[index + start];
          }
          return result2;
        }

        function baseSome(collection, predicate) {
          var result2;
          baseEach(collection, function (value, index, collection2) {
            result2 = predicate(value, index, collection2);
            return !result2;
          });
          return !!result2;
        }

        function baseSortedIndex(array, value, retHighest) {
          var low = 0, high = array == null ? low : array.length;
          if (typeof value == "number" && value === value && high <= HALF_MAX_ARRAY_LENGTH) {
            while (low < high) {
              var mid = low + high >>> 1, computed = array[mid];
              if (computed !== null && !isSymbol(computed) && (retHighest ? computed <= value : computed < value)) {
                low = mid + 1;
              } else {
                high = mid;
              }
            }
            return high;
          }
          return baseSortedIndexBy(array, value, identity, retHighest);
        }

        function baseSortedIndexBy(array, value, iteratee2, retHighest) {
          var low = 0, high = array == null ? 0 : array.length;
          if (high === 0) {
            return 0;
          }
          value = iteratee2(value);
          var valIsNaN = value !== value, valIsNull = value === null, valIsSymbol = isSymbol(value),
            valIsUndefined = value === undefined$1;
          while (low < high) {
            var mid = nativeFloor((low + high) / 2), computed = iteratee2(array[mid]),
              othIsDefined = computed !== undefined$1, othIsNull = computed === null,
              othIsReflexive = computed === computed, othIsSymbol = isSymbol(computed);
            if (valIsNaN) {
              var setLow = retHighest || othIsReflexive;
            } else if (valIsUndefined) {
              setLow = othIsReflexive && (retHighest || othIsDefined);
            } else if (valIsNull) {
              setLow = othIsReflexive && othIsDefined && (retHighest || !othIsNull);
            } else if (valIsSymbol) {
              setLow = othIsReflexive && othIsDefined && !othIsNull && (retHighest || !othIsSymbol);
            } else if (othIsNull || othIsSymbol) {
              setLow = false;
            } else {
              setLow = retHighest ? computed <= value : computed < value;
            }
            if (setLow) {
              low = mid + 1;
            } else {
              high = mid;
            }
          }
          return nativeMin(high, MAX_ARRAY_INDEX);
        }

        function baseSortedUniq(array, iteratee2) {
          var index = -1, length = array.length, resIndex = 0, result2 = [];
          while (++index < length) {
            var value = array[index], computed = iteratee2 ? iteratee2(value) : value;
            if (!index || !eq(computed, seen)) {
              var seen = computed;
              result2[resIndex++] = value === 0 ? 0 : value;
            }
          }
          return result2;
        }

        function baseToNumber(value) {
          if (typeof value == "number") {
            return value;
          }
          if (isSymbol(value)) {
            return NAN;
          }
          return +value;
        }

        function baseToString(value) {
          if (typeof value == "string") {
            return value;
          }
          if (isArray(value)) {
            return arrayMap(value, baseToString) + "";
          }
          if (isSymbol(value)) {
            return symbolToString ? symbolToString.call(value) : "";
          }
          var result2 = value + "";
          return result2 == "0" && 1 / value == -INFINITY ? "-0" : result2;
        }

        function baseUniq(array, iteratee2, comparator) {
          var index = -1, includes2 = arrayIncludes, length = array.length, isCommon = true, result2 = [],
            seen = result2;
          if (comparator) {
            isCommon = false;
            includes2 = arrayIncludesWith;
          } else if (length >= LARGE_ARRAY_SIZE) {
            var set2 = iteratee2 ? null : createSet(array);
            if (set2) {
              return setToArray(set2);
            }
            isCommon = false;
            includes2 = cacheHas;
            seen = new SetCache();
          } else {
            seen = iteratee2 ? [] : result2;
          }
          outer:
            while (++index < length) {
              var value = array[index], computed = iteratee2 ? iteratee2(value) : value;
              value = comparator || value !== 0 ? value : 0;
              if (isCommon && computed === computed) {
                var seenIndex = seen.length;
                while (seenIndex--) {
                  if (seen[seenIndex] === computed) {
                    continue outer;
                  }
                }
                if (iteratee2) {
                  seen.push(computed);
                }
                result2.push(value);
              } else if (!includes2(seen, computed, comparator)) {
                if (seen !== result2) {
                  seen.push(computed);
                }
                result2.push(value);
              }
            }
          return result2;
        }

        function baseUnset(object, path) {
          path = castPath(path, object);
          object = parent(object, path);
          return object == null || delete object[toKey(last(path))];
        }

        function baseUpdate(object, path, updater, customizer) {
          return baseSet(object, path, updater(baseGet(object, path)), customizer);
        }

        function baseWhile(array, predicate, isDrop, fromRight) {
          var length = array.length, index = fromRight ? length : -1;
          while ((fromRight ? index-- : ++index < length) && predicate(array[index], index, array)) {
          }
          return isDrop ? baseSlice(array, fromRight ? 0 : index, fromRight ? index + 1 : length) : baseSlice(array, fromRight ? index + 1 : 0, fromRight ? length : index);
        }

        function baseWrapperValue(value, actions) {
          var result2 = value;
          if (result2 instanceof LazyWrapper) {
            result2 = result2.value();
          }
          return arrayReduce(actions, function (result3, action) {
            return action.func.apply(action.thisArg, arrayPush([result3], action.args));
          }, result2);
        }

        function baseXor(arrays, iteratee2, comparator) {
          var length = arrays.length;
          if (length < 2) {
            return length ? baseUniq(arrays[0]) : [];
          }
          var index = -1, result2 = Array2(length);
          while (++index < length) {
            var array = arrays[index], othIndex = -1;
            while (++othIndex < length) {
              if (othIndex != index) {
                result2[index] = baseDifference(result2[index] || array, arrays[othIndex], iteratee2, comparator);
              }
            }
          }
          return baseUniq(baseFlatten(result2, 1), iteratee2, comparator);
        }

        function baseZipObject(props, values2, assignFunc) {
          var index = -1, length = props.length, valsLength = values2.length, result2 = {};
          while (++index < length) {
            var value = index < valsLength ? values2[index] : undefined$1;
            assignFunc(result2, props[index], value);
          }
          return result2;
        }

        function castArrayLikeObject(value) {
          return isArrayLikeObject(value) ? value : [];
        }

        function castFunction(value) {
          return typeof value == "function" ? value : identity;
        }

        function castPath(value, object) {
          if (isArray(value)) {
            return value;
          }
          return isKey(value, object) ? [value] : stringToPath(toString(value));
        }

        var castRest = baseRest;

        function castSlice(array, start, end) {
          var length = array.length;
          end = end === undefined$1 ? length : end;
          return !start && end >= length ? array : baseSlice(array, start, end);
        }

        var clearTimeout = ctxClearTimeout || function (id) {
          return root.clearTimeout(id);
        };

        function cloneBuffer(buffer, isDeep) {
          if (isDeep) {
            return buffer.slice();
          }
          var length = buffer.length, result2 = allocUnsafe ? allocUnsafe(length) : new buffer.constructor(length);
          buffer.copy(result2);
          return result2;
        }

        function cloneArrayBuffer(arrayBuffer) {
          var result2 = new arrayBuffer.constructor(arrayBuffer.byteLength);
          new Uint8Array2(result2).set(new Uint8Array2(arrayBuffer));
          return result2;
        }

        function cloneDataView(dataView, isDeep) {
          var buffer = isDeep ? cloneArrayBuffer(dataView.buffer) : dataView.buffer;
          return new dataView.constructor(buffer, dataView.byteOffset, dataView.byteLength);
        }

        function cloneRegExp(regexp) {
          var result2 = new regexp.constructor(regexp.source, reFlags.exec(regexp));
          result2.lastIndex = regexp.lastIndex;
          return result2;
        }

        function cloneSymbol(symbol) {
          return symbolValueOf ? Object2(symbolValueOf.call(symbol)) : {};
        }

        function cloneTypedArray(typedArray, isDeep) {
          var buffer = isDeep ? cloneArrayBuffer(typedArray.buffer) : typedArray.buffer;
          return new typedArray.constructor(buffer, typedArray.byteOffset, typedArray.length);
        }

        function compareAscending(value, other) {
          if (value !== other) {
            var valIsDefined = value !== undefined$1, valIsNull = value === null, valIsReflexive = value === value,
              valIsSymbol = isSymbol(value);
            var othIsDefined = other !== undefined$1, othIsNull = other === null, othIsReflexive = other === other,
              othIsSymbol = isSymbol(other);
            if (!othIsNull && !othIsSymbol && !valIsSymbol && value > other || valIsSymbol && othIsDefined && othIsReflexive && !othIsNull && !othIsSymbol || valIsNull && othIsDefined && othIsReflexive || !valIsDefined && othIsReflexive || !valIsReflexive) {
              return 1;
            }
            if (!valIsNull && !valIsSymbol && !othIsSymbol && value < other || othIsSymbol && valIsDefined && valIsReflexive && !valIsNull && !valIsSymbol || othIsNull && valIsDefined && valIsReflexive || !othIsDefined && valIsReflexive || !othIsReflexive) {
              return -1;
            }
          }
          return 0;
        }

        function compareMultiple(object, other, orders) {
          var index = -1, objCriteria = object.criteria, othCriteria = other.criteria, length = objCriteria.length,
            ordersLength = orders.length;
          while (++index < length) {
            var result2 = compareAscending(objCriteria[index], othCriteria[index]);
            if (result2) {
              if (index >= ordersLength) {
                return result2;
              }
              var order = orders[index];
              return result2 * (order == "desc" ? -1 : 1);
            }
          }
          return object.index - other.index;
        }

        function composeArgs(args, partials, holders, isCurried) {
          var argsIndex = -1, argsLength = args.length, holdersLength = holders.length, leftIndex = -1,
            leftLength = partials.length, rangeLength = nativeMax(argsLength - holdersLength, 0),
            result2 = Array2(leftLength + rangeLength), isUncurried = !isCurried;
          while (++leftIndex < leftLength) {
            result2[leftIndex] = partials[leftIndex];
          }
          while (++argsIndex < holdersLength) {
            if (isUncurried || argsIndex < argsLength) {
              result2[holders[argsIndex]] = args[argsIndex];
            }
          }
          while (rangeLength--) {
            result2[leftIndex++] = args[argsIndex++];
          }
          return result2;
        }

        function composeArgsRight(args, partials, holders, isCurried) {
          var argsIndex = -1, argsLength = args.length, holdersIndex = -1, holdersLength = holders.length,
            rightIndex = -1, rightLength = partials.length, rangeLength = nativeMax(argsLength - holdersLength, 0),
            result2 = Array2(rangeLength + rightLength), isUncurried = !isCurried;
          while (++argsIndex < rangeLength) {
            result2[argsIndex] = args[argsIndex];
          }
          var offset = argsIndex;
          while (++rightIndex < rightLength) {
            result2[offset + rightIndex] = partials[rightIndex];
          }
          while (++holdersIndex < holdersLength) {
            if (isUncurried || argsIndex < argsLength) {
              result2[offset + holders[holdersIndex]] = args[argsIndex++];
            }
          }
          return result2;
        }

        function copyArray(source, array) {
          var index = -1, length = source.length;
          array || (array = Array2(length));
          while (++index < length) {
            array[index] = source[index];
          }
          return array;
        }

        function copyObject(source, props, object, customizer) {
          var isNew = !object;
          object || (object = {});
          var index = -1, length = props.length;
          while (++index < length) {
            var key = props[index];
            var newValue = customizer ? customizer(object[key], source[key], key, object, source) : undefined$1;
            if (newValue === undefined$1) {
              newValue = source[key];
            }
            if (isNew) {
              baseAssignValue(object, key, newValue);
            } else {
              assignValue(object, key, newValue);
            }
          }
          return object;
        }

        function copySymbols(source, object) {
          return copyObject(source, getSymbols(source), object);
        }

        function copySymbolsIn(source, object) {
          return copyObject(source, getSymbolsIn(source), object);
        }

        function createAggregator(setter, initializer) {
          return function (collection, iteratee2) {
            var func = isArray(collection) ? arrayAggregator : baseAggregator,
              accumulator = initializer ? initializer() : {};
            return func(collection, setter, getIteratee(iteratee2, 2), accumulator);
          };
        }

        function createAssigner(assigner) {
          return baseRest(function (object, sources) {
            var index = -1, length = sources.length, customizer = length > 1 ? sources[length - 1] : undefined$1,
              guard = length > 2 ? sources[2] : undefined$1;
            customizer = assigner.length > 3 && typeof customizer == "function" ? (length--, customizer) : undefined$1;
            if (guard && isIterateeCall(sources[0], sources[1], guard)) {
              customizer = length < 3 ? undefined$1 : customizer;
              length = 1;
            }
            object = Object2(object);
            while (++index < length) {
              var source = sources[index];
              if (source) {
                assigner(object, source, index, customizer);
              }
            }
            return object;
          });
        }

        function createBaseEach(eachFunc, fromRight) {
          return function (collection, iteratee2) {
            if (collection == null) {
              return collection;
            }
            if (!isArrayLike(collection)) {
              return eachFunc(collection, iteratee2);
            }
            var length = collection.length, index = fromRight ? length : -1, iterable = Object2(collection);
            while (fromRight ? index-- : ++index < length) {
              if (iteratee2(iterable[index], index, iterable) === false) {
                break;
              }
            }
            return collection;
          };
        }

        function createBaseFor(fromRight) {
          return function (object, iteratee2, keysFunc) {
            var index = -1, iterable = Object2(object), props = keysFunc(object), length = props.length;
            while (length--) {
              var key = props[fromRight ? length : ++index];
              if (iteratee2(iterable[key], key, iterable) === false) {
                break;
              }
            }
            return object;
          };
        }

        function createBind(func, bitmask, thisArg) {
          var isBind = bitmask & WRAP_BIND_FLAG, Ctor = createCtor(func);

          function wrapper() {
            var fn = this && this !== root && this instanceof wrapper ? Ctor : func;
            return fn.apply(isBind ? thisArg : this, arguments);
          }

          return wrapper;
        }

        function createCaseFirst(methodName) {
          return function (string) {
            string = toString(string);
            var strSymbols = hasUnicode(string) ? stringToArray(string) : undefined$1;
            var chr = strSymbols ? strSymbols[0] : string.charAt(0);
            var trailing = strSymbols ? castSlice(strSymbols, 1).join("") : string.slice(1);
            return chr[methodName]() + trailing;
          };
        }

        function createCompounder(callback) {
          return function (string) {
            return arrayReduce(words(deburr(string).replace(reApos, "")), callback, "");
          };
        }

        function createCtor(Ctor) {
          return function () {
            var args = arguments;
            switch (args.length) {
              case 0:
                return new Ctor();
              case 1:
                return new Ctor(args[0]);
              case 2:
                return new Ctor(args[0], args[1]);
              case 3:
                return new Ctor(args[0], args[1], args[2]);
              case 4:
                return new Ctor(args[0], args[1], args[2], args[3]);
              case 5:
                return new Ctor(args[0], args[1], args[2], args[3], args[4]);
              case 6:
                return new Ctor(args[0], args[1], args[2], args[3], args[4], args[5]);
              case 7:
                return new Ctor(args[0], args[1], args[2], args[3], args[4], args[5], args[6]);
            }
            var thisBinding = baseCreate(Ctor.prototype), result2 = Ctor.apply(thisBinding, args);
            return isObject(result2) ? result2 : thisBinding;
          };
        }

        function createCurry(func, bitmask, arity) {
          var Ctor = createCtor(func);

          function wrapper() {
            var length = arguments.length, args = Array2(length), index = length, placeholder = getHolder(wrapper);
            while (index--) {
              args[index] = arguments[index];
            }
            var holders = length < 3 && args[0] !== placeholder && args[length - 1] !== placeholder ? [] : replaceHolders(args, placeholder);
            length -= holders.length;
            if (length < arity) {
              return createRecurry(
                func,
                bitmask,
                createHybrid,
                wrapper.placeholder,
                undefined$1,
                args,
                holders,
                undefined$1,
                undefined$1,
                arity - length
              );
            }
            var fn = this && this !== root && this instanceof wrapper ? Ctor : func;
            return apply(fn, this, args);
          }

          return wrapper;
        }

        function createFind(findIndexFunc) {
          return function (collection, predicate, fromIndex) {
            var iterable = Object2(collection);
            if (!isArrayLike(collection)) {
              var iteratee2 = getIteratee(predicate, 3);
              collection = keys(collection);
              predicate = function (key) {
                return iteratee2(iterable[key], key, iterable);
              };
            }
            var index = findIndexFunc(collection, predicate, fromIndex);
            return index > -1 ? iterable[iteratee2 ? collection[index] : index] : undefined$1;
          };
        }

        function createFlow(fromRight) {
          return flatRest(function (funcs) {
            var length = funcs.length, index = length, prereq = LodashWrapper.prototype.thru;
            if (fromRight) {
              funcs.reverse();
            }
            while (index--) {
              var func = funcs[index];
              if (typeof func != "function") {
                throw new TypeError2(FUNC_ERROR_TEXT);
              }
              if (prereq && !wrapper && getFuncName(func) == "wrapper") {
                var wrapper = new LodashWrapper([], true);
              }
            }
            index = wrapper ? index : length;
            while (++index < length) {
              func = funcs[index];
              var funcName = getFuncName(func), data = funcName == "wrapper" ? getData(func) : undefined$1;
              if (data && isLaziable(data[0]) && data[1] == (WRAP_ARY_FLAG | WRAP_CURRY_FLAG | WRAP_PARTIAL_FLAG | WRAP_REARG_FLAG) && !data[4].length && data[9] == 1) {
                wrapper = wrapper[getFuncName(data[0])].apply(wrapper, data[3]);
              } else {
                wrapper = func.length == 1 && isLaziable(func) ? wrapper[funcName]() : wrapper.thru(func);
              }
            }
            return function () {
              var args = arguments, value = args[0];
              if (wrapper && args.length == 1 && isArray(value)) {
                return wrapper.plant(value).value();
              }
              var index2 = 0, result2 = length ? funcs[index2].apply(this, args) : value;
              while (++index2 < length) {
                result2 = funcs[index2].call(this, result2);
              }
              return result2;
            };
          });
        }

        function createHybrid(func, bitmask, thisArg, partials, holders, partialsRight, holdersRight, argPos, ary2, arity) {
          var isAry = bitmask & WRAP_ARY_FLAG, isBind = bitmask & WRAP_BIND_FLAG,
            isBindKey = bitmask & WRAP_BIND_KEY_FLAG, isCurried = bitmask & (WRAP_CURRY_FLAG | WRAP_CURRY_RIGHT_FLAG),
            isFlip = bitmask & WRAP_FLIP_FLAG, Ctor = isBindKey ? undefined$1 : createCtor(func);

          function wrapper() {
            var length = arguments.length, args = Array2(length), index = length;
            while (index--) {
              args[index] = arguments[index];
            }
            if (isCurried) {
              var placeholder = getHolder(wrapper), holdersCount = countHolders(args, placeholder);
            }
            if (partials) {
              args = composeArgs(args, partials, holders, isCurried);
            }
            if (partialsRight) {
              args = composeArgsRight(args, partialsRight, holdersRight, isCurried);
            }
            length -= holdersCount;
            if (isCurried && length < arity) {
              var newHolders = replaceHolders(args, placeholder);
              return createRecurry(
                func,
                bitmask,
                createHybrid,
                wrapper.placeholder,
                thisArg,
                args,
                newHolders,
                argPos,
                ary2,
                arity - length
              );
            }
            var thisBinding = isBind ? thisArg : this, fn = isBindKey ? thisBinding[func] : func;
            length = args.length;
            if (argPos) {
              args = reorder(args, argPos);
            } else if (isFlip && length > 1) {
              args.reverse();
            }
            if (isAry && ary2 < length) {
              args.length = ary2;
            }
            if (this && this !== root && this instanceof wrapper) {
              fn = Ctor || createCtor(fn);
            }
            return fn.apply(thisBinding, args);
          }

          return wrapper;
        }

        function createInverter(setter, toIteratee) {
          return function (object, iteratee2) {
            return baseInverter(object, setter, toIteratee(iteratee2), {});
          };
        }

        function createMathOperation(operator, defaultValue) {
          return function (value, other) {
            var result2;
            if (value === undefined$1 && other === undefined$1) {
              return defaultValue;
            }
            if (value !== undefined$1) {
              result2 = value;
            }
            if (other !== undefined$1) {
              if (result2 === undefined$1) {
                return other;
              }
              if (typeof value == "string" || typeof other == "string") {
                value = baseToString(value);
                other = baseToString(other);
              } else {
                value = baseToNumber(value);
                other = baseToNumber(other);
              }
              result2 = operator(value, other);
            }
            return result2;
          };
        }

        function createOver(arrayFunc) {
          return flatRest(function (iteratees) {
            iteratees = arrayMap(iteratees, baseUnary(getIteratee()));
            return baseRest(function (args) {
              var thisArg = this;
              return arrayFunc(iteratees, function (iteratee2) {
                return apply(iteratee2, thisArg, args);
              });
            });
          });
        }

        function createPadding(length, chars) {
          chars = chars === undefined$1 ? " " : baseToString(chars);
          var charsLength = chars.length;
          if (charsLength < 2) {
            return charsLength ? baseRepeat(chars, length) : chars;
          }
          var result2 = baseRepeat(chars, nativeCeil(length / stringSize(chars)));
          return hasUnicode(chars) ? castSlice(stringToArray(result2), 0, length).join("") : result2.slice(0, length);
        }

        function createPartial(func, bitmask, thisArg, partials) {
          var isBind = bitmask & WRAP_BIND_FLAG, Ctor = createCtor(func);

          function wrapper() {
            var argsIndex = -1, argsLength = arguments.length, leftIndex = -1, leftLength = partials.length,
              args = Array2(leftLength + argsLength),
              fn = this && this !== root && this instanceof wrapper ? Ctor : func;
            while (++leftIndex < leftLength) {
              args[leftIndex] = partials[leftIndex];
            }
            while (argsLength--) {
              args[leftIndex++] = arguments[++argsIndex];
            }
            return apply(fn, isBind ? thisArg : this, args);
          }

          return wrapper;
        }

        function createRange(fromRight) {
          return function (start, end, step) {
            if (step && typeof step != "number" && isIterateeCall(start, end, step)) {
              end = step = undefined$1;
            }
            start = toFinite(start);
            if (end === undefined$1) {
              end = start;
              start = 0;
            } else {
              end = toFinite(end);
            }
            step = step === undefined$1 ? start < end ? 1 : -1 : toFinite(step);
            return baseRange(start, end, step, fromRight);
          };
        }

        function createRelationalOperation(operator) {
          return function (value, other) {
            if (!(typeof value == "string" && typeof other == "string")) {
              value = toNumber(value);
              other = toNumber(other);
            }
            return operator(value, other);
          };
        }

        function createRecurry(func, bitmask, wrapFunc, placeholder, thisArg, partials, holders, argPos, ary2, arity) {
          var isCurry = bitmask & WRAP_CURRY_FLAG, newHolders = isCurry ? holders : undefined$1,
            newHoldersRight = isCurry ? undefined$1 : holders, newPartials = isCurry ? partials : undefined$1,
            newPartialsRight = isCurry ? undefined$1 : partials;
          bitmask |= isCurry ? WRAP_PARTIAL_FLAG : WRAP_PARTIAL_RIGHT_FLAG;
          bitmask &= ~(isCurry ? WRAP_PARTIAL_RIGHT_FLAG : WRAP_PARTIAL_FLAG);
          if (!(bitmask & WRAP_CURRY_BOUND_FLAG)) {
            bitmask &= ~(WRAP_BIND_FLAG | WRAP_BIND_KEY_FLAG);
          }
          var newData = [
            func,
            bitmask,
            thisArg,
            newPartials,
            newHolders,
            newPartialsRight,
            newHoldersRight,
            argPos,
            ary2,
            arity
          ];
          var result2 = wrapFunc.apply(undefined$1, newData);
          if (isLaziable(func)) {
            setData(result2, newData);
          }
          result2.placeholder = placeholder;
          return setWrapToString(result2, func, bitmask);
        }

        function createRound(methodName) {
          var func = Math2[methodName];
          return function (number, precision) {
            number = toNumber(number);
            precision = precision == null ? 0 : nativeMin(toInteger(precision), 292);
            if (precision && nativeIsFinite(number)) {
              var pair = (toString(number) + "e").split("e"), value = func(pair[0] + "e" + (+pair[1] + precision));
              pair = (toString(value) + "e").split("e");
              return +(pair[0] + "e" + (+pair[1] - precision));
            }
            return func(number);
          };
        }

        var createSet = !(Set2 && 1 / setToArray(new Set2([, -0]))[1] == INFINITY) ? noop : function (values2) {
          return new Set2(values2);
        };

        function createToPairs(keysFunc) {
          return function (object) {
            var tag = getTag(object);
            if (tag == mapTag) {
              return mapToArray(object);
            }
            if (tag == setTag) {
              return setToPairs(object);
            }
            return baseToPairs(object, keysFunc(object));
          };
        }

        function createWrap(func, bitmask, thisArg, partials, holders, argPos, ary2, arity) {
          var isBindKey = bitmask & WRAP_BIND_KEY_FLAG;
          if (!isBindKey && typeof func != "function") {
            throw new TypeError2(FUNC_ERROR_TEXT);
          }
          var length = partials ? partials.length : 0;
          if (!length) {
            bitmask &= ~(WRAP_PARTIAL_FLAG | WRAP_PARTIAL_RIGHT_FLAG);
            partials = holders = undefined$1;
          }
          ary2 = ary2 === undefined$1 ? ary2 : nativeMax(toInteger(ary2), 0);
          arity = arity === undefined$1 ? arity : toInteger(arity);
          length -= holders ? holders.length : 0;
          if (bitmask & WRAP_PARTIAL_RIGHT_FLAG) {
            var partialsRight = partials, holdersRight = holders;
            partials = holders = undefined$1;
          }
          var data = isBindKey ? undefined$1 : getData(func);
          var newData = [
            func,
            bitmask,
            thisArg,
            partials,
            holders,
            partialsRight,
            holdersRight,
            argPos,
            ary2,
            arity
          ];
          if (data) {
            mergeData(newData, data);
          }
          func = newData[0];
          bitmask = newData[1];
          thisArg = newData[2];
          partials = newData[3];
          holders = newData[4];
          arity = newData[9] = newData[9] === undefined$1 ? isBindKey ? 0 : func.length : nativeMax(newData[9] - length, 0);
          if (!arity && bitmask & (WRAP_CURRY_FLAG | WRAP_CURRY_RIGHT_FLAG)) {
            bitmask &= ~(WRAP_CURRY_FLAG | WRAP_CURRY_RIGHT_FLAG);
          }
          if (!bitmask || bitmask == WRAP_BIND_FLAG) {
            var result2 = createBind(func, bitmask, thisArg);
          } else if (bitmask == WRAP_CURRY_FLAG || bitmask == WRAP_CURRY_RIGHT_FLAG) {
            result2 = createCurry(func, bitmask, arity);
          } else if ((bitmask == WRAP_PARTIAL_FLAG || bitmask == (WRAP_BIND_FLAG | WRAP_PARTIAL_FLAG)) && !holders.length) {
            result2 = createPartial(func, bitmask, thisArg, partials);
          } else {
            result2 = createHybrid.apply(undefined$1, newData);
          }
          var setter = data ? baseSetData : setData;
          return setWrapToString(setter(result2, newData), func, bitmask);
        }

        function customDefaultsAssignIn(objValue, srcValue, key, object) {
          if (objValue === undefined$1 || eq(objValue, objectProto[key]) && !hasOwnProperty.call(object, key)) {
            return srcValue;
          }
          return objValue;
        }

        function customDefaultsMerge(objValue, srcValue, key, object, source, stack) {
          if (isObject(objValue) && isObject(srcValue)) {
            stack.set(srcValue, objValue);
            baseMerge(objValue, srcValue, undefined$1, customDefaultsMerge, stack);
            stack["delete"](srcValue);
          }
          return objValue;
        }

        function customOmitClone(value) {
          return isPlainObject(value) ? undefined$1 : value;
        }

        function equalArrays(array, other, bitmask, customizer, equalFunc, stack) {
          var isPartial = bitmask & COMPARE_PARTIAL_FLAG, arrLength = array.length, othLength = other.length;
          if (arrLength != othLength && !(isPartial && othLength > arrLength)) {
            return false;
          }
          var arrStacked = stack.get(array);
          var othStacked = stack.get(other);
          if (arrStacked && othStacked) {
            return arrStacked == other && othStacked == array;
          }
          var index = -1, result2 = true, seen = bitmask & COMPARE_UNORDERED_FLAG ? new SetCache() : undefined$1;
          stack.set(array, other);
          stack.set(other, array);
          while (++index < arrLength) {
            var arrValue = array[index], othValue = other[index];
            if (customizer) {
              var compared = isPartial ? customizer(othValue, arrValue, index, other, array, stack) : customizer(arrValue, othValue, index, array, other, stack);
            }
            if (compared !== undefined$1) {
              if (compared) {
                continue;
              }
              result2 = false;
              break;
            }
            if (seen) {
              if (!arraySome(other, function (othValue2, othIndex) {
                if (!cacheHas(seen, othIndex) && (arrValue === othValue2 || equalFunc(arrValue, othValue2, bitmask, customizer, stack))) {
                  return seen.push(othIndex);
                }
              })) {
                result2 = false;
                break;
              }
            } else if (!(arrValue === othValue || equalFunc(arrValue, othValue, bitmask, customizer, stack))) {
              result2 = false;
              break;
            }
          }
          stack["delete"](array);
          stack["delete"](other);
          return result2;
        }

        function equalByTag(object, other, tag, bitmask, customizer, equalFunc, stack) {
          switch (tag) {
            case dataViewTag:
              if (object.byteLength != other.byteLength || object.byteOffset != other.byteOffset) {
                return false;
              }
              object = object.buffer;
              other = other.buffer;
            case arrayBufferTag:
              if (object.byteLength != other.byteLength || !equalFunc(new Uint8Array2(object), new Uint8Array2(other))) {
                return false;
              }
              return true;
            case boolTag:
            case dateTag:
            case numberTag:
              return eq(+object, +other);
            case errorTag:
              return object.name == other.name && object.message == other.message;
            case regexpTag:
            case stringTag:
              return object == other + "";
            case mapTag:
              var convert = mapToArray;
            case setTag:
              var isPartial = bitmask & COMPARE_PARTIAL_FLAG;
              convert || (convert = setToArray);
              if (object.size != other.size && !isPartial) {
                return false;
              }
              var stacked = stack.get(object);
              if (stacked) {
                return stacked == other;
              }
              bitmask |= COMPARE_UNORDERED_FLAG;
              stack.set(object, other);
              var result2 = equalArrays(convert(object), convert(other), bitmask, customizer, equalFunc, stack);
              stack["delete"](object);
              return result2;
            case symbolTag:
              if (symbolValueOf) {
                return symbolValueOf.call(object) == symbolValueOf.call(other);
              }
          }
          return false;
        }

        function equalObjects(object, other, bitmask, customizer, equalFunc, stack) {
          var isPartial = bitmask & COMPARE_PARTIAL_FLAG, objProps = getAllKeys(object), objLength = objProps.length,
            othProps = getAllKeys(other), othLength = othProps.length;
          if (objLength != othLength && !isPartial) {
            return false;
          }
          var index = objLength;
          while (index--) {
            var key = objProps[index];
            if (!(isPartial ? key in other : hasOwnProperty.call(other, key))) {
              return false;
            }
          }
          var objStacked = stack.get(object);
          var othStacked = stack.get(other);
          if (objStacked && othStacked) {
            return objStacked == other && othStacked == object;
          }
          var result2 = true;
          stack.set(object, other);
          stack.set(other, object);
          var skipCtor = isPartial;
          while (++index < objLength) {
            key = objProps[index];
            var objValue = object[key], othValue = other[key];
            if (customizer) {
              var compared = isPartial ? customizer(othValue, objValue, key, other, object, stack) : customizer(objValue, othValue, key, object, other, stack);
            }
            if (!(compared === undefined$1 ? objValue === othValue || equalFunc(objValue, othValue, bitmask, customizer, stack) : compared)) {
              result2 = false;
              break;
            }
            skipCtor || (skipCtor = key == "constructor");
          }
          if (result2 && !skipCtor) {
            var objCtor = object.constructor, othCtor = other.constructor;
            if (objCtor != othCtor && ("constructor" in object && "constructor" in other) && !(typeof objCtor == "function" && objCtor instanceof objCtor && typeof othCtor == "function" && othCtor instanceof othCtor)) {
              result2 = false;
            }
          }
          stack["delete"](object);
          stack["delete"](other);
          return result2;
        }

        function flatRest(func) {
          return setToString(overRest(func, undefined$1, flatten), func + "");
        }

        function getAllKeys(object) {
          return baseGetAllKeys(object, keys, getSymbols);
        }

        function getAllKeysIn(object) {
          return baseGetAllKeys(object, keysIn, getSymbolsIn);
        }

        var getData = !metaMap ? noop : function (func) {
          return metaMap.get(func);
        };

        function getFuncName(func) {
          var result2 = func.name + "", array = realNames[result2],
            length = hasOwnProperty.call(realNames, result2) ? array.length : 0;
          while (length--) {
            var data = array[length], otherFunc = data.func;
            if (otherFunc == null || otherFunc == func) {
              return data.name;
            }
          }
          return result2;
        }

        function getHolder(func) {
          var object = hasOwnProperty.call(lodash2, "placeholder") ? lodash2 : func;
          return object.placeholder;
        }

        function getIteratee() {
          var result2 = lodash2.iteratee || iteratee;
          result2 = result2 === iteratee ? baseIteratee : result2;
          return arguments.length ? result2(arguments[0], arguments[1]) : result2;
        }

        function getMapData(map2, key) {
          var data = map2.__data__;
          return isKeyable(key) ? data[typeof key == "string" ? "string" : "hash"] : data.map;
        }

        function getMatchData(object) {
          var result2 = keys(object), length = result2.length;
          while (length--) {
            var key = result2[length], value = object[key];
            result2[length] = [key, value, isStrictComparable(value)];
          }
          return result2;
        }

        function getNative(object, key) {
          var value = getValue(object, key);
          return baseIsNative(value) ? value : undefined$1;
        }

        function getRawTag(value) {
          var isOwn = hasOwnProperty.call(value, symToStringTag), tag = value[symToStringTag];
          try {
            value[symToStringTag] = undefined$1;
            var unmasked = true;
          } catch (e) {
          }
          var result2 = nativeObjectToString.call(value);
          if (unmasked) {
            if (isOwn) {
              value[symToStringTag] = tag;
            } else {
              delete value[symToStringTag];
            }
          }
          return result2;
        }

        var getSymbols = !nativeGetSymbols ? stubArray : function (object) {
          if (object == null) {
            return [];
          }
          object = Object2(object);
          return arrayFilter(nativeGetSymbols(object), function (symbol) {
            return propertyIsEnumerable.call(object, symbol);
          });
        };
        var getSymbolsIn = !nativeGetSymbols ? stubArray : function (object) {
          var result2 = [];
          while (object) {
            arrayPush(result2, getSymbols(object));
            object = getPrototype(object);
          }
          return result2;
        };
        var getTag = baseGetTag;
        if (DataView && getTag(new DataView(new ArrayBuffer(1))) != dataViewTag || Map2 && getTag(new Map2()) != mapTag || Promise2 && getTag(Promise2.resolve()) != promiseTag || Set2 && getTag(new Set2()) != setTag || WeakMap2 && getTag(new WeakMap2()) != weakMapTag) {
          getTag = function (value) {
            var result2 = baseGetTag(value), Ctor = result2 == objectTag ? value.constructor : undefined$1,
              ctorString = Ctor ? toSource(Ctor) : "";
            if (ctorString) {
              switch (ctorString) {
                case dataViewCtorString:
                  return dataViewTag;
                case mapCtorString:
                  return mapTag;
                case promiseCtorString:
                  return promiseTag;
                case setCtorString:
                  return setTag;
                case weakMapCtorString:
                  return weakMapTag;
              }
            }
            return result2;
          };
        }

        function getView(start, end, transforms) {
          var index = -1, length = transforms.length;
          while (++index < length) {
            var data = transforms[index], size2 = data.size;
            switch (data.type) {
              case "drop":
                start += size2;
                break;
              case "dropRight":
                end -= size2;
                break;
              case "take":
                end = nativeMin(end, start + size2);
                break;
              case "takeRight":
                start = nativeMax(start, end - size2);
                break;
            }
          }
          return {"start": start, "end": end};
        }

        function getWrapDetails(source) {
          var match = source.match(reWrapDetails);
          return match ? match[1].split(reSplitDetails) : [];
        }

        function hasPath(object, path, hasFunc) {
          path = castPath(path, object);
          var index = -1, length = path.length, result2 = false;
          while (++index < length) {
            var key = toKey(path[index]);
            if (!(result2 = object != null && hasFunc(object, key))) {
              break;
            }
            object = object[key];
          }
          if (result2 || ++index != length) {
            return result2;
          }
          length = object == null ? 0 : object.length;
          return !!length && isLength(length) && isIndex(key, length) && (isArray(object) || isArguments(object));
        }

        function initCloneArray(array) {
          var length = array.length, result2 = new array.constructor(length);
          if (length && typeof array[0] == "string" && hasOwnProperty.call(array, "index")) {
            result2.index = array.index;
            result2.input = array.input;
          }
          return result2;
        }

        function initCloneObject(object) {
          return typeof object.constructor == "function" && !isPrototype(object) ? baseCreate(getPrototype(object)) : {};
        }

        function initCloneByTag(object, tag, isDeep) {
          var Ctor = object.constructor;
          switch (tag) {
            case arrayBufferTag:
              return cloneArrayBuffer(object);
            case boolTag:
            case dateTag:
              return new Ctor(+object);
            case dataViewTag:
              return cloneDataView(object, isDeep);
            case float32Tag:
            case float64Tag:
            case int8Tag:
            case int16Tag:
            case int32Tag:
            case uint8Tag:
            case uint8ClampedTag:
            case uint16Tag:
            case uint32Tag:
              return cloneTypedArray(object, isDeep);
            case mapTag:
              return new Ctor();
            case numberTag:
            case stringTag:
              return new Ctor(object);
            case regexpTag:
              return cloneRegExp(object);
            case setTag:
              return new Ctor();
            case symbolTag:
              return cloneSymbol(object);
          }
        }

        function insertWrapDetails(source, details) {
          var length = details.length;
          if (!length) {
            return source;
          }
          var lastIndex = length - 1;
          details[lastIndex] = (length > 1 ? "& " : "") + details[lastIndex];
          details = details.join(length > 2 ? ", " : " ");
          return source.replace(reWrapComment, "{\n/* [wrapped with " + details + "] */\n");
        }

        function isFlattenable(value) {
          return isArray(value) || isArguments(value) || !!(spreadableSymbol && value && value[spreadableSymbol]);
        }

        function isIndex(value, length) {
          var type = typeof value;
          length = length == null ? MAX_SAFE_INTEGER : length;
          return !!length && (type == "number" || type != "symbol" && reIsUint.test(value)) && (value > -1 && value % 1 == 0 && value < length);
        }

        function isIterateeCall(value, index, object) {
          if (!isObject(object)) {
            return false;
          }
          var type = typeof index;
          if (type == "number" ? isArrayLike(object) && isIndex(index, object.length) : type == "string" && index in object) {
            return eq(object[index], value);
          }
          return false;
        }

        function isKey(value, object) {
          if (isArray(value)) {
            return false;
          }
          var type = typeof value;
          if (type == "number" || type == "symbol" || type == "boolean" || value == null || isSymbol(value)) {
            return true;
          }
          return reIsPlainProp.test(value) || !reIsDeepProp.test(value) || object != null && value in Object2(object);
        }

        function isKeyable(value) {
          var type = typeof value;
          return type == "string" || type == "number" || type == "symbol" || type == "boolean" ? value !== "__proto__" : value === null;
        }

        function isLaziable(func) {
          var funcName = getFuncName(func), other = lodash2[funcName];
          if (typeof other != "function" || !(funcName in LazyWrapper.prototype)) {
            return false;
          }
          if (func === other) {
            return true;
          }
          var data = getData(other);
          return !!data && func === data[0];
        }

        function isMasked(func) {
          return !!maskSrcKey && maskSrcKey in func;
        }

        var isMaskable = coreJsData ? isFunction : stubFalse;

        function isPrototype(value) {
          var Ctor = value && value.constructor, proto = typeof Ctor == "function" && Ctor.prototype || objectProto;
          return value === proto;
        }

        function isStrictComparable(value) {
          return value === value && !isObject(value);
        }

        function matchesStrictComparable(key, srcValue) {
          return function (object) {
            if (object == null) {
              return false;
            }
            return object[key] === srcValue && (srcValue !== undefined$1 || key in Object2(object));
          };
        }

        function memoizeCapped(func) {
          var result2 = memoize2(func, function (key) {
            if (cache.size === MAX_MEMOIZE_SIZE) {
              cache.clear();
            }
            return key;
          });
          var cache = result2.cache;
          return result2;
        }

        function mergeData(data, source) {
          var bitmask = data[1], srcBitmask = source[1], newBitmask = bitmask | srcBitmask,
            isCommon = newBitmask < (WRAP_BIND_FLAG | WRAP_BIND_KEY_FLAG | WRAP_ARY_FLAG);
          var isCombo = srcBitmask == WRAP_ARY_FLAG && bitmask == WRAP_CURRY_FLAG || srcBitmask == WRAP_ARY_FLAG && bitmask == WRAP_REARG_FLAG && data[7].length <= source[8] || srcBitmask == (WRAP_ARY_FLAG | WRAP_REARG_FLAG) && source[7].length <= source[8] && bitmask == WRAP_CURRY_FLAG;
          if (!(isCommon || isCombo)) {
            return data;
          }
          if (srcBitmask & WRAP_BIND_FLAG) {
            data[2] = source[2];
            newBitmask |= bitmask & WRAP_BIND_FLAG ? 0 : WRAP_CURRY_BOUND_FLAG;
          }
          var value = source[3];
          if (value) {
            var partials = data[3];
            data[3] = partials ? composeArgs(partials, value, source[4]) : value;
            data[4] = partials ? replaceHolders(data[3], PLACEHOLDER) : source[4];
          }
          value = source[5];
          if (value) {
            partials = data[5];
            data[5] = partials ? composeArgsRight(partials, value, source[6]) : value;
            data[6] = partials ? replaceHolders(data[5], PLACEHOLDER) : source[6];
          }
          value = source[7];
          if (value) {
            data[7] = value;
          }
          if (srcBitmask & WRAP_ARY_FLAG) {
            data[8] = data[8] == null ? source[8] : nativeMin(data[8], source[8]);
          }
          if (data[9] == null) {
            data[9] = source[9];
          }
          data[0] = source[0];
          data[1] = newBitmask;
          return data;
        }

        function nativeKeysIn(object) {
          var result2 = [];
          if (object != null) {
            for (var key in Object2(object)) {
              result2.push(key);
            }
          }
          return result2;
        }

        function objectToString(value) {
          return nativeObjectToString.call(value);
        }

        function overRest(func, start, transform2) {
          start = nativeMax(start === undefined$1 ? func.length - 1 : start, 0);
          return function () {
            var args = arguments, index = -1, length = nativeMax(args.length - start, 0), array = Array2(length);
            while (++index < length) {
              array[index] = args[start + index];
            }
            index = -1;
            var otherArgs = Array2(start + 1);
            while (++index < start) {
              otherArgs[index] = args[index];
            }
            otherArgs[start] = transform2(array);
            return apply(func, this, otherArgs);
          };
        }

        function parent(object, path) {
          return path.length < 2 ? object : baseGet(object, baseSlice(path, 0, -1));
        }

        function reorder(array, indexes) {
          var arrLength = array.length, length = nativeMin(indexes.length, arrLength), oldArray = copyArray(array);
          while (length--) {
            var index = indexes[length];
            array[length] = isIndex(index, arrLength) ? oldArray[index] : undefined$1;
          }
          return array;
        }

        function safeGet(object, key) {
          if (key === "constructor" && typeof object[key] === "function") {
            return;
          }
          if (key == "__proto__") {
            return;
          }
          return object[key];
        }

        var setData = shortOut(baseSetData);
        var setTimeout = ctxSetTimeout || function (func, wait) {
          return root.setTimeout(func, wait);
        };
        var setToString = shortOut(baseSetToString);

        function setWrapToString(wrapper, reference, bitmask) {
          var source = reference + "";
          return setToString(wrapper, insertWrapDetails(source, updateWrapDetails(getWrapDetails(source), bitmask)));
        }

        function shortOut(func) {
          var count = 0, lastCalled = 0;
          return function () {
            var stamp = nativeNow(), remaining = HOT_SPAN - (stamp - lastCalled);
            lastCalled = stamp;
            if (remaining > 0) {
              if (++count >= HOT_COUNT) {
                return arguments[0];
              }
            } else {
              count = 0;
            }
            return func.apply(undefined$1, arguments);
          };
        }

        function shuffleSelf(array, size2) {
          var index = -1, length = array.length, lastIndex = length - 1;
          size2 = size2 === undefined$1 ? length : size2;
          while (++index < size2) {
            var rand = baseRandom(index, lastIndex), value = array[rand];
            array[rand] = array[index];
            array[index] = value;
          }
          array.length = size2;
          return array;
        }

        var stringToPath = memoizeCapped(function (string) {
          var result2 = [];
          if (string.charCodeAt(0) === 46) {
            result2.push("");
          }
          string.replace(rePropName, function (match, number, quote, subString) {
            result2.push(quote ? subString.replace(reEscapeChar, "$1") : number || match);
          });
          return result2;
        });

        function toKey(value) {
          if (typeof value == "string" || isSymbol(value)) {
            return value;
          }
          var result2 = value + "";
          return result2 == "0" && 1 / value == -INFINITY ? "-0" : result2;
        }

        function toSource(func) {
          if (func != null) {
            try {
              return funcToString.call(func);
            } catch (e) {
            }
            try {
              return func + "";
            } catch (e) {
            }
          }
          return "";
        }

        function updateWrapDetails(details, bitmask) {
          arrayEach(wrapFlags, function (pair) {
            var value = "_." + pair[0];
            if (bitmask & pair[1] && !arrayIncludes(details, value)) {
              details.push(value);
            }
          });
          return details.sort();
        }

        function wrapperClone(wrapper) {
          if (wrapper instanceof LazyWrapper) {
            return wrapper.clone();
          }
          var result2 = new LodashWrapper(wrapper.__wrapped__, wrapper.__chain__);
          result2.__actions__ = copyArray(wrapper.__actions__);
          result2.__index__ = wrapper.__index__;
          result2.__values__ = wrapper.__values__;
          return result2;
        }

        function chunk(array, size2, guard) {
          if (guard ? isIterateeCall(array, size2, guard) : size2 === undefined$1) {
            size2 = 1;
          } else {
            size2 = nativeMax(toInteger(size2), 0);
          }
          var length = array == null ? 0 : array.length;
          if (!length || size2 < 1) {
            return [];
          }
          var index = 0, resIndex = 0, result2 = Array2(nativeCeil(length / size2));
          while (index < length) {
            result2[resIndex++] = baseSlice(array, index, index += size2);
          }
          return result2;
        }

        function compact(array) {
          var index = -1, length = array == null ? 0 : array.length, resIndex = 0, result2 = [];
          while (++index < length) {
            var value = array[index];
            if (value) {
              result2[resIndex++] = value;
            }
          }
          return result2;
        }

        function concat() {
          var length = arguments.length;
          if (!length) {
            return [];
          }
          var args = Array2(length - 1), array = arguments[0], index = length;
          while (index--) {
            args[index - 1] = arguments[index];
          }
          return arrayPush(isArray(array) ? copyArray(array) : [array], baseFlatten(args, 1));
        }

        var difference = baseRest(function (array, values2) {
          return isArrayLikeObject(array) ? baseDifference(array, baseFlatten(values2, 1, isArrayLikeObject, true)) : [];
        });
        var differenceBy = baseRest(function (array, values2) {
          var iteratee2 = last(values2);
          if (isArrayLikeObject(iteratee2)) {
            iteratee2 = undefined$1;
          }
          return isArrayLikeObject(array) ? baseDifference(array, baseFlatten(values2, 1, isArrayLikeObject, true), getIteratee(iteratee2, 2)) : [];
        });
        var differenceWith = baseRest(function (array, values2) {
          var comparator = last(values2);
          if (isArrayLikeObject(comparator)) {
            comparator = undefined$1;
          }
          return isArrayLikeObject(array) ? baseDifference(array, baseFlatten(values2, 1, isArrayLikeObject, true), undefined$1, comparator) : [];
        });

        function drop(array, n, guard) {
          var length = array == null ? 0 : array.length;
          if (!length) {
            return [];
          }
          n = guard || n === undefined$1 ? 1 : toInteger(n);
          return baseSlice(array, n < 0 ? 0 : n, length);
        }

        function dropRight(array, n, guard) {
          var length = array == null ? 0 : array.length;
          if (!length) {
            return [];
          }
          n = guard || n === undefined$1 ? 1 : toInteger(n);
          n = length - n;
          return baseSlice(array, 0, n < 0 ? 0 : n);
        }

        function dropRightWhile(array, predicate) {
          return array && array.length ? baseWhile(array, getIteratee(predicate, 3), true, true) : [];
        }

        function dropWhile(array, predicate) {
          return array && array.length ? baseWhile(array, getIteratee(predicate, 3), true) : [];
        }

        function fill(array, value, start, end) {
          var length = array == null ? 0 : array.length;
          if (!length) {
            return [];
          }
          if (start && typeof start != "number" && isIterateeCall(array, value, start)) {
            start = 0;
            end = length;
          }
          return baseFill(array, value, start, end);
        }

        function findIndex(array, predicate, fromIndex) {
          var length = array == null ? 0 : array.length;
          if (!length) {
            return -1;
          }
          var index = fromIndex == null ? 0 : toInteger(fromIndex);
          if (index < 0) {
            index = nativeMax(length + index, 0);
          }
          return baseFindIndex(array, getIteratee(predicate, 3), index);
        }

        function findLastIndex(array, predicate, fromIndex) {
          var length = array == null ? 0 : array.length;
          if (!length) {
            return -1;
          }
          var index = length - 1;
          if (fromIndex !== undefined$1) {
            index = toInteger(fromIndex);
            index = fromIndex < 0 ? nativeMax(length + index, 0) : nativeMin(index, length - 1);
          }
          return baseFindIndex(array, getIteratee(predicate, 3), index, true);
        }

        function flatten(array) {
          var length = array == null ? 0 : array.length;
          return length ? baseFlatten(array, 1) : [];
        }

        function flattenDeep(array) {
          var length = array == null ? 0 : array.length;
          return length ? baseFlatten(array, INFINITY) : [];
        }

        function flattenDepth(array, depth) {
          var length = array == null ? 0 : array.length;
          if (!length) {
            return [];
          }
          depth = depth === undefined$1 ? 1 : toInteger(depth);
          return baseFlatten(array, depth);
        }

        function fromPairs(pairs) {
          var index = -1, length = pairs == null ? 0 : pairs.length, result2 = {};
          while (++index < length) {
            var pair = pairs[index];
            result2[pair[0]] = pair[1];
          }
          return result2;
        }

        function head(array) {
          return array && array.length ? array[0] : undefined$1;
        }

        function indexOf(array, value, fromIndex) {
          var length = array == null ? 0 : array.length;
          if (!length) {
            return -1;
          }
          var index = fromIndex == null ? 0 : toInteger(fromIndex);
          if (index < 0) {
            index = nativeMax(length + index, 0);
          }
          return baseIndexOf(array, value, index);
        }

        function initial(array) {
          var length = array == null ? 0 : array.length;
          return length ? baseSlice(array, 0, -1) : [];
        }

        var intersection = baseRest(function (arrays) {
          var mapped = arrayMap(arrays, castArrayLikeObject);
          return mapped.length && mapped[0] === arrays[0] ? baseIntersection(mapped) : [];
        });
        var intersectionBy = baseRest(function (arrays) {
          var iteratee2 = last(arrays), mapped = arrayMap(arrays, castArrayLikeObject);
          if (iteratee2 === last(mapped)) {
            iteratee2 = undefined$1;
          } else {
            mapped.pop();
          }
          return mapped.length && mapped[0] === arrays[0] ? baseIntersection(mapped, getIteratee(iteratee2, 2)) : [];
        });
        var intersectionWith = baseRest(function (arrays) {
          var comparator = last(arrays), mapped = arrayMap(arrays, castArrayLikeObject);
          comparator = typeof comparator == "function" ? comparator : undefined$1;
          if (comparator) {
            mapped.pop();
          }
          return mapped.length && mapped[0] === arrays[0] ? baseIntersection(mapped, undefined$1, comparator) : [];
        });

        function join(array, separator) {
          return array == null ? "" : nativeJoin.call(array, separator);
        }

        function last(array) {
          var length = array == null ? 0 : array.length;
          return length ? array[length - 1] : undefined$1;
        }

        function lastIndexOf(array, value, fromIndex) {
          var length = array == null ? 0 : array.length;
          if (!length) {
            return -1;
          }
          var index = length;
          if (fromIndex !== undefined$1) {
            index = toInteger(fromIndex);
            index = index < 0 ? nativeMax(length + index, 0) : nativeMin(index, length - 1);
          }
          return value === value ? strictLastIndexOf(array, value, index) : baseFindIndex(array, baseIsNaN, index, true);
        }

        function nth(array, n) {
          return array && array.length ? baseNth(array, toInteger(n)) : undefined$1;
        }

        var pull = baseRest(pullAll);

        function pullAll(array, values2) {
          return array && array.length && values2 && values2.length ? basePullAll(array, values2) : array;
        }

        function pullAllBy(array, values2, iteratee2) {
          return array && array.length && values2 && values2.length ? basePullAll(array, values2, getIteratee(iteratee2, 2)) : array;
        }

        function pullAllWith(array, values2, comparator) {
          return array && array.length && values2 && values2.length ? basePullAll(array, values2, undefined$1, comparator) : array;
        }

        var pullAt = flatRest(function (array, indexes) {
          var length = array == null ? 0 : array.length, result2 = baseAt(array, indexes);
          basePullAt(array, arrayMap(indexes, function (index) {
            return isIndex(index, length) ? +index : index;
          }).sort(compareAscending));
          return result2;
        });

        function remove(array, predicate) {
          var result2 = [];
          if (!(array && array.length)) {
            return result2;
          }
          var index = -1, indexes = [], length = array.length;
          predicate = getIteratee(predicate, 3);
          while (++index < length) {
            var value = array[index];
            if (predicate(value, index, array)) {
              result2.push(value);
              indexes.push(index);
            }
          }
          basePullAt(array, indexes);
          return result2;
        }

        function reverse(array) {
          return array == null ? array : nativeReverse.call(array);
        }

        function slice(array, start, end) {
          var length = array == null ? 0 : array.length;
          if (!length) {
            return [];
          }
          if (end && typeof end != "number" && isIterateeCall(array, start, end)) {
            start = 0;
            end = length;
          } else {
            start = start == null ? 0 : toInteger(start);
            end = end === undefined$1 ? length : toInteger(end);
          }
          return baseSlice(array, start, end);
        }

        function sortedIndex(array, value) {
          return baseSortedIndex(array, value);
        }

        function sortedIndexBy(array, value, iteratee2) {
          return baseSortedIndexBy(array, value, getIteratee(iteratee2, 2));
        }

        function sortedIndexOf(array, value) {
          var length = array == null ? 0 : array.length;
          if (length) {
            var index = baseSortedIndex(array, value);
            if (index < length && eq(array[index], value)) {
              return index;
            }
          }
          return -1;
        }

        function sortedLastIndex(array, value) {
          return baseSortedIndex(array, value, true);
        }

        function sortedLastIndexBy(array, value, iteratee2) {
          return baseSortedIndexBy(array, value, getIteratee(iteratee2, 2), true);
        }

        function sortedLastIndexOf(array, value) {
          var length = array == null ? 0 : array.length;
          if (length) {
            var index = baseSortedIndex(array, value, true) - 1;
            if (eq(array[index], value)) {
              return index;
            }
          }
          return -1;
        }

        function sortedUniq(array) {
          return array && array.length ? baseSortedUniq(array) : [];
        }

        function sortedUniqBy(array, iteratee2) {
          return array && array.length ? baseSortedUniq(array, getIteratee(iteratee2, 2)) : [];
        }

        function tail(array) {
          var length = array == null ? 0 : array.length;
          return length ? baseSlice(array, 1, length) : [];
        }

        function take(array, n, guard) {
          if (!(array && array.length)) {
            return [];
          }
          n = guard || n === undefined$1 ? 1 : toInteger(n);
          return baseSlice(array, 0, n < 0 ? 0 : n);
        }

        function takeRight(array, n, guard) {
          var length = array == null ? 0 : array.length;
          if (!length) {
            return [];
          }
          n = guard || n === undefined$1 ? 1 : toInteger(n);
          n = length - n;
          return baseSlice(array, n < 0 ? 0 : n, length);
        }

        function takeRightWhile(array, predicate) {
          return array && array.length ? baseWhile(array, getIteratee(predicate, 3), false, true) : [];
        }

        function takeWhile(array, predicate) {
          return array && array.length ? baseWhile(array, getIteratee(predicate, 3)) : [];
        }

        var union = baseRest(function (arrays) {
          return baseUniq(baseFlatten(arrays, 1, isArrayLikeObject, true));
        });
        var unionBy = baseRest(function (arrays) {
          var iteratee2 = last(arrays);
          if (isArrayLikeObject(iteratee2)) {
            iteratee2 = undefined$1;
          }
          return baseUniq(baseFlatten(arrays, 1, isArrayLikeObject, true), getIteratee(iteratee2, 2));
        });
        var unionWith = baseRest(function (arrays) {
          var comparator = last(arrays);
          comparator = typeof comparator == "function" ? comparator : undefined$1;
          return baseUniq(baseFlatten(arrays, 1, isArrayLikeObject, true), undefined$1, comparator);
        });

        function uniq(array) {
          return array && array.length ? baseUniq(array) : [];
        }

        function uniqBy(array, iteratee2) {
          return array && array.length ? baseUniq(array, getIteratee(iteratee2, 2)) : [];
        }

        function uniqWith(array, comparator) {
          comparator = typeof comparator == "function" ? comparator : undefined$1;
          return array && array.length ? baseUniq(array, undefined$1, comparator) : [];
        }

        function unzip(array) {
          if (!(array && array.length)) {
            return [];
          }
          var length = 0;
          array = arrayFilter(array, function (group) {
            if (isArrayLikeObject(group)) {
              length = nativeMax(group.length, length);
              return true;
            }
          });
          return baseTimes(length, function (index) {
            return arrayMap(array, baseProperty(index));
          });
        }

        function unzipWith(array, iteratee2) {
          if (!(array && array.length)) {
            return [];
          }
          var result2 = unzip(array);
          if (iteratee2 == null) {
            return result2;
          }
          return arrayMap(result2, function (group) {
            return apply(iteratee2, undefined$1, group);
          });
        }

        var without = baseRest(function (array, values2) {
          return isArrayLikeObject(array) ? baseDifference(array, values2) : [];
        });
        var xor = baseRest(function (arrays) {
          return baseXor(arrayFilter(arrays, isArrayLikeObject));
        });
        var xorBy = baseRest(function (arrays) {
          var iteratee2 = last(arrays);
          if (isArrayLikeObject(iteratee2)) {
            iteratee2 = undefined$1;
          }
          return baseXor(arrayFilter(arrays, isArrayLikeObject), getIteratee(iteratee2, 2));
        });
        var xorWith = baseRest(function (arrays) {
          var comparator = last(arrays);
          comparator = typeof comparator == "function" ? comparator : undefined$1;
          return baseXor(arrayFilter(arrays, isArrayLikeObject), undefined$1, comparator);
        });
        var zip = baseRest(unzip);

        function zipObject(props, values2) {
          return baseZipObject(props || [], values2 || [], assignValue);
        }

        function zipObjectDeep(props, values2) {
          return baseZipObject(props || [], values2 || [], baseSet);
        }

        var zipWith = baseRest(function (arrays) {
          var length = arrays.length, iteratee2 = length > 1 ? arrays[length - 1] : undefined$1;
          iteratee2 = typeof iteratee2 == "function" ? (arrays.pop(), iteratee2) : undefined$1;
          return unzipWith(arrays, iteratee2);
        });

        function chain(value) {
          var result2 = lodash2(value);
          result2.__chain__ = true;
          return result2;
        }

        function tap(value, interceptor) {
          interceptor(value);
          return value;
        }

        function thru(value, interceptor) {
          return interceptor(value);
        }

        var wrapperAt = flatRest(function (paths) {
          var length = paths.length, start = length ? paths[0] : 0, value = this.__wrapped__,
            interceptor = function (object) {
              return baseAt(object, paths);
            };
          if (length > 1 || this.__actions__.length || !(value instanceof LazyWrapper) || !isIndex(start)) {
            return this.thru(interceptor);
          }
          value = value.slice(start, +start + (length ? 1 : 0));
          value.__actions__.push({
            "func": thru,
            "args": [interceptor],
            "thisArg": undefined$1
          });
          return new LodashWrapper(value, this.__chain__).thru(function (array) {
            if (length && !array.length) {
              array.push(undefined$1);
            }
            return array;
          });
        });

        function wrapperChain() {
          return chain(this);
        }

        function wrapperCommit() {
          return new LodashWrapper(this.value(), this.__chain__);
        }

        function wrapperNext() {
          if (this.__values__ === undefined$1) {
            this.__values__ = toArray(this.value());
          }
          var done = this.__index__ >= this.__values__.length,
            value = done ? undefined$1 : this.__values__[this.__index__++];
          return {"done": done, "value": value};
        }

        function wrapperToIterator() {
          return this;
        }

        function wrapperPlant(value) {
          var result2, parent2 = this;
          while (parent2 instanceof baseLodash) {
            var clone2 = wrapperClone(parent2);
            clone2.__index__ = 0;
            clone2.__values__ = undefined$1;
            if (result2) {
              previous.__wrapped__ = clone2;
            } else {
              result2 = clone2;
            }
            var previous = clone2;
            parent2 = parent2.__wrapped__;
          }
          previous.__wrapped__ = value;
          return result2;
        }

        function wrapperReverse() {
          var value = this.__wrapped__;
          if (value instanceof LazyWrapper) {
            var wrapped = value;
            if (this.__actions__.length) {
              wrapped = new LazyWrapper(this);
            }
            wrapped = wrapped.reverse();
            wrapped.__actions__.push({
              "func": thru,
              "args": [reverse],
              "thisArg": undefined$1
            });
            return new LodashWrapper(wrapped, this.__chain__);
          }
          return this.thru(reverse);
        }

        function wrapperValue() {
          return baseWrapperValue(this.__wrapped__, this.__actions__);
        }

        var countBy = createAggregator(function (result2, value, key) {
          if (hasOwnProperty.call(result2, key)) {
            ++result2[key];
          } else {
            baseAssignValue(result2, key, 1);
          }
        });

        function every(collection, predicate, guard) {
          var func = isArray(collection) ? arrayEvery : baseEvery;
          if (guard && isIterateeCall(collection, predicate, guard)) {
            predicate = undefined$1;
          }
          return func(collection, getIteratee(predicate, 3));
        }

        function filter(collection, predicate) {
          var func = isArray(collection) ? arrayFilter : baseFilter;
          return func(collection, getIteratee(predicate, 3));
        }

        var find = createFind(findIndex);
        var findLast = createFind(findLastIndex);

        function flatMap(collection, iteratee2) {
          return baseFlatten(map(collection, iteratee2), 1);
        }

        function flatMapDeep(collection, iteratee2) {
          return baseFlatten(map(collection, iteratee2), INFINITY);
        }

        function flatMapDepth(collection, iteratee2, depth) {
          depth = depth === undefined$1 ? 1 : toInteger(depth);
          return baseFlatten(map(collection, iteratee2), depth);
        }

        function forEach(collection, iteratee2) {
          var func = isArray(collection) ? arrayEach : baseEach;
          return func(collection, getIteratee(iteratee2, 3));
        }

        function forEachRight(collection, iteratee2) {
          var func = isArray(collection) ? arrayEachRight : baseEachRight;
          return func(collection, getIteratee(iteratee2, 3));
        }

        var groupBy = createAggregator(function (result2, value, key) {
          if (hasOwnProperty.call(result2, key)) {
            result2[key].push(value);
          } else {
            baseAssignValue(result2, key, [value]);
          }
        });

        function includes(collection, value, fromIndex, guard) {
          collection = isArrayLike(collection) ? collection : values(collection);
          fromIndex = fromIndex && !guard ? toInteger(fromIndex) : 0;
          var length = collection.length;
          if (fromIndex < 0) {
            fromIndex = nativeMax(length + fromIndex, 0);
          }
          return isString(collection) ? fromIndex <= length && collection.indexOf(value, fromIndex) > -1 : !!length && baseIndexOf(collection, value, fromIndex) > -1;
        }

        var invokeMap = baseRest(function (collection, path, args) {
          var index = -1, isFunc = typeof path == "function",
            result2 = isArrayLike(collection) ? Array2(collection.length) : [];
          baseEach(collection, function (value) {
            result2[++index] = isFunc ? apply(path, value, args) : baseInvoke(value, path, args);
          });
          return result2;
        });
        var keyBy = createAggregator(function (result2, value, key) {
          baseAssignValue(result2, key, value);
        });

        function map(collection, iteratee2) {
          var func = isArray(collection) ? arrayMap : baseMap;
          return func(collection, getIteratee(iteratee2, 3));
        }

        function orderBy(collection, iteratees, orders, guard) {
          if (collection == null) {
            return [];
          }
          if (!isArray(iteratees)) {
            iteratees = iteratees == null ? [] : [iteratees];
          }
          orders = guard ? undefined$1 : orders;
          if (!isArray(orders)) {
            orders = orders == null ? [] : [orders];
          }
          return baseOrderBy(collection, iteratees, orders);
        }

        var partition = createAggregator(function (result2, value, key) {
          result2[key ? 0 : 1].push(value);
        }, function () {
          return [[], []];
        });

        function reduce(collection, iteratee2, accumulator) {
          var func = isArray(collection) ? arrayReduce : baseReduce, initAccum = arguments.length < 3;
          return func(collection, getIteratee(iteratee2, 4), accumulator, initAccum, baseEach);
        }

        function reduceRight(collection, iteratee2, accumulator) {
          var func = isArray(collection) ? arrayReduceRight : baseReduce, initAccum = arguments.length < 3;
          return func(collection, getIteratee(iteratee2, 4), accumulator, initAccum, baseEachRight);
        }

        function reject(collection, predicate) {
          var func = isArray(collection) ? arrayFilter : baseFilter;
          return func(collection, negate(getIteratee(predicate, 3)));
        }

        function sample(collection) {
          var func = isArray(collection) ? arraySample : baseSample;
          return func(collection);
        }

        function sampleSize(collection, n, guard) {
          if (guard ? isIterateeCall(collection, n, guard) : n === undefined$1) {
            n = 1;
          } else {
            n = toInteger(n);
          }
          var func = isArray(collection) ? arraySampleSize : baseSampleSize;
          return func(collection, n);
        }

        function shuffle(collection) {
          var func = isArray(collection) ? arrayShuffle : baseShuffle;
          return func(collection);
        }

        function size(collection) {
          if (collection == null) {
            return 0;
          }
          if (isArrayLike(collection)) {
            return isString(collection) ? stringSize(collection) : collection.length;
          }
          var tag = getTag(collection);
          if (tag == mapTag || tag == setTag) {
            return collection.size;
          }
          return baseKeys(collection).length;
        }

        function some(collection, predicate, guard) {
          var func = isArray(collection) ? arraySome : baseSome;
          if (guard && isIterateeCall(collection, predicate, guard)) {
            predicate = undefined$1;
          }
          return func(collection, getIteratee(predicate, 3));
        }

        var sortBy = baseRest(function (collection, iteratees) {
          if (collection == null) {
            return [];
          }
          var length = iteratees.length;
          if (length > 1 && isIterateeCall(collection, iteratees[0], iteratees[1])) {
            iteratees = [];
          } else if (length > 2 && isIterateeCall(iteratees[0], iteratees[1], iteratees[2])) {
            iteratees = [iteratees[0]];
          }
          return baseOrderBy(collection, baseFlatten(iteratees, 1), []);
        });
        var now = ctxNow || function () {
          return root.Date.now();
        };

        function after(n, func) {
          if (typeof func != "function") {
            throw new TypeError2(FUNC_ERROR_TEXT);
          }
          n = toInteger(n);
          return function () {
            if (--n < 1) {
              return func.apply(this, arguments);
            }
          };
        }

        function ary(func, n, guard) {
          n = guard ? undefined$1 : n;
          n = func && n == null ? func.length : n;
          return createWrap(func, WRAP_ARY_FLAG, undefined$1, undefined$1, undefined$1, undefined$1, n);
        }

        function before(n, func) {
          var result2;
          if (typeof func != "function") {
            throw new TypeError2(FUNC_ERROR_TEXT);
          }
          n = toInteger(n);
          return function () {
            if (--n > 0) {
              result2 = func.apply(this, arguments);
            }
            if (n <= 1) {
              func = undefined$1;
            }
            return result2;
          };
        }

        var bind = baseRest(function (func, thisArg, partials) {
          var bitmask = WRAP_BIND_FLAG;
          if (partials.length) {
            var holders = replaceHolders(partials, getHolder(bind));
            bitmask |= WRAP_PARTIAL_FLAG;
          }
          return createWrap(func, bitmask, thisArg, partials, holders);
        });
        var bindKey = baseRest(function (object, key, partials) {
          var bitmask = WRAP_BIND_FLAG | WRAP_BIND_KEY_FLAG;
          if (partials.length) {
            var holders = replaceHolders(partials, getHolder(bindKey));
            bitmask |= WRAP_PARTIAL_FLAG;
          }
          return createWrap(key, bitmask, object, partials, holders);
        });

        function curry(func, arity, guard) {
          arity = guard ? undefined$1 : arity;
          var result2 = createWrap(func, WRAP_CURRY_FLAG, undefined$1, undefined$1, undefined$1, undefined$1, undefined$1, arity);
          result2.placeholder = curry.placeholder;
          return result2;
        }

        function curryRight(func, arity, guard) {
          arity = guard ? undefined$1 : arity;
          var result2 = createWrap(func, WRAP_CURRY_RIGHT_FLAG, undefined$1, undefined$1, undefined$1, undefined$1, undefined$1, arity);
          result2.placeholder = curryRight.placeholder;
          return result2;
        }

        function debounce(func, wait, options) {
          var lastArgs, lastThis, maxWait, result2, timerId, lastCallTime, lastInvokeTime = 0, leading = false,
            maxing = false, trailing = true;
          if (typeof func != "function") {
            throw new TypeError2(FUNC_ERROR_TEXT);
          }
          wait = toNumber(wait) || 0;
          if (isObject(options)) {
            leading = !!options.leading;
            maxing = "maxWait" in options;
            maxWait = maxing ? nativeMax(toNumber(options.maxWait) || 0, wait) : maxWait;
            trailing = "trailing" in options ? !!options.trailing : trailing;
          }

          function invokeFunc(time) {
            var args = lastArgs, thisArg = lastThis;
            lastArgs = lastThis = undefined$1;
            lastInvokeTime = time;
            result2 = func.apply(thisArg, args);
            return result2;
          }

          function leadingEdge(time) {
            lastInvokeTime = time;
            timerId = setTimeout(timerExpired, wait);
            return leading ? invokeFunc(time) : result2;
          }

          function remainingWait(time) {
            var timeSinceLastCall = time - lastCallTime, timeSinceLastInvoke = time - lastInvokeTime,
              timeWaiting = wait - timeSinceLastCall;
            return maxing ? nativeMin(timeWaiting, maxWait - timeSinceLastInvoke) : timeWaiting;
          }

          function shouldInvoke(time) {
            var timeSinceLastCall = time - lastCallTime, timeSinceLastInvoke = time - lastInvokeTime;
            return lastCallTime === undefined$1 || timeSinceLastCall >= wait || timeSinceLastCall < 0 || maxing && timeSinceLastInvoke >= maxWait;
          }

          function timerExpired() {
            var time = now();
            if (shouldInvoke(time)) {
              return trailingEdge(time);
            }
            timerId = setTimeout(timerExpired, remainingWait(time));
          }

          function trailingEdge(time) {
            timerId = undefined$1;
            if (trailing && lastArgs) {
              return invokeFunc(time);
            }
            lastArgs = lastThis = undefined$1;
            return result2;
          }

          function cancel() {
            if (timerId !== undefined$1) {
              clearTimeout(timerId);
            }
            lastInvokeTime = 0;
            lastArgs = lastCallTime = lastThis = timerId = undefined$1;
          }

          function flush() {
            return timerId === undefined$1 ? result2 : trailingEdge(now());
          }

          function debounced() {
            var time = now(), isInvoking = shouldInvoke(time);
            lastArgs = arguments;
            lastThis = this;
            lastCallTime = time;
            if (isInvoking) {
              if (timerId === undefined$1) {
                return leadingEdge(lastCallTime);
              }
              if (maxing) {
                clearTimeout(timerId);
                timerId = setTimeout(timerExpired, wait);
                return invokeFunc(lastCallTime);
              }
            }
            if (timerId === undefined$1) {
              timerId = setTimeout(timerExpired, wait);
            }
            return result2;
          }

          debounced.cancel = cancel;
          debounced.flush = flush;
          return debounced;
        }

        var defer = baseRest(function (func, args) {
          return baseDelay(func, 1, args);
        });
        var delay = baseRest(function (func, wait, args) {
          return baseDelay(func, toNumber(wait) || 0, args);
        });

        function flip(func) {
          return createWrap(func, WRAP_FLIP_FLAG);
        }

        function memoize2(func, resolver) {
          if (typeof func != "function" || resolver != null && typeof resolver != "function") {
            throw new TypeError2(FUNC_ERROR_TEXT);
          }
          var memoized = function () {
            var args = arguments, key = resolver ? resolver.apply(this, args) : args[0], cache = memoized.cache;
            if (cache.has(key)) {
              return cache.get(key);
            }
            var result2 = func.apply(this, args);
            memoized.cache = cache.set(key, result2) || cache;
            return result2;
          };
          memoized.cache = new (memoize2.Cache || MapCache)();
          return memoized;
        }

        memoize2.Cache = MapCache;

        function negate(predicate) {
          if (typeof predicate != "function") {
            throw new TypeError2(FUNC_ERROR_TEXT);
          }
          return function () {
            var args = arguments;
            switch (args.length) {
              case 0:
                return !predicate.call(this);
              case 1:
                return !predicate.call(this, args[0]);
              case 2:
                return !predicate.call(this, args[0], args[1]);
              case 3:
                return !predicate.call(this, args[0], args[1], args[2]);
            }
            return !predicate.apply(this, args);
          };
        }

        function once(func) {
          return before(2, func);
        }

        var overArgs = castRest(function (func, transforms) {
          transforms = transforms.length == 1 && isArray(transforms[0]) ? arrayMap(transforms[0], baseUnary(getIteratee())) : arrayMap(baseFlatten(transforms, 1), baseUnary(getIteratee()));
          var funcsLength = transforms.length;
          return baseRest(function (args) {
            var index = -1, length = nativeMin(args.length, funcsLength);
            while (++index < length) {
              args[index] = transforms[index].call(this, args[index]);
            }
            return apply(func, this, args);
          });
        });
        var partial = baseRest(function (func, partials) {
          var holders = replaceHolders(partials, getHolder(partial));
          return createWrap(func, WRAP_PARTIAL_FLAG, undefined$1, partials, holders);
        });
        var partialRight = baseRest(function (func, partials) {
          var holders = replaceHolders(partials, getHolder(partialRight));
          return createWrap(func, WRAP_PARTIAL_RIGHT_FLAG, undefined$1, partials, holders);
        });
        var rearg = flatRest(function (func, indexes) {
          return createWrap(func, WRAP_REARG_FLAG, undefined$1, undefined$1, undefined$1, indexes);
        });

        function rest(func, start) {
          if (typeof func != "function") {
            throw new TypeError2(FUNC_ERROR_TEXT);
          }
          start = start === undefined$1 ? start : toInteger(start);
          return baseRest(func, start);
        }

        function spread(func, start) {
          if (typeof func != "function") {
            throw new TypeError2(FUNC_ERROR_TEXT);
          }
          start = start == null ? 0 : nativeMax(toInteger(start), 0);
          return baseRest(function (args) {
            var array = args[start], otherArgs = castSlice(args, 0, start);
            if (array) {
              arrayPush(otherArgs, array);
            }
            return apply(func, this, otherArgs);
          });
        }

        function throttle(func, wait, options) {
          var leading = true, trailing = true;
          if (typeof func != "function") {
            throw new TypeError2(FUNC_ERROR_TEXT);
          }
          if (isObject(options)) {
            leading = "leading" in options ? !!options.leading : leading;
            trailing = "trailing" in options ? !!options.trailing : trailing;
          }
          return debounce(func, wait, {
            "leading": leading,
            "maxWait": wait,
            "trailing": trailing
          });
        }

        function unary(func) {
          return ary(func, 1);
        }

        function wrap(value, wrapper) {
          return partial(castFunction(wrapper), value);
        }

        function castArray() {
          if (!arguments.length) {
            return [];
          }
          var value = arguments[0];
          return isArray(value) ? value : [value];
        }

        function clone(value) {
          return baseClone(value, CLONE_SYMBOLS_FLAG);
        }

        function cloneWith(value, customizer) {
          customizer = typeof customizer == "function" ? customizer : undefined$1;
          return baseClone(value, CLONE_SYMBOLS_FLAG, customizer);
        }

        function cloneDeep(value) {
          return baseClone(value, CLONE_DEEP_FLAG | CLONE_SYMBOLS_FLAG);
        }

        function cloneDeepWith(value, customizer) {
          customizer = typeof customizer == "function" ? customizer : undefined$1;
          return baseClone(value, CLONE_DEEP_FLAG | CLONE_SYMBOLS_FLAG, customizer);
        }

        function conformsTo(object, source) {
          return source == null || baseConformsTo(object, source, keys(source));
        }

        function eq(value, other) {
          return value === other || value !== value && other !== other;
        }

        var gt = createRelationalOperation(baseGt);
        var gte = createRelationalOperation(function (value, other) {
          return value >= other;
        });
        var isArguments = baseIsArguments(function () {
          return arguments;
        }()) ? baseIsArguments : function (value) {
          return isObjectLike(value) && hasOwnProperty.call(value, "callee") && !propertyIsEnumerable.call(value, "callee");
        };
        var isArray = Array2.isArray;
        var isArrayBuffer = nodeIsArrayBuffer ? baseUnary(nodeIsArrayBuffer) : baseIsArrayBuffer;

        function isArrayLike(value) {
          return value != null && isLength(value.length) && !isFunction(value);
        }

        function isArrayLikeObject(value) {
          return isObjectLike(value) && isArrayLike(value);
        }

        function isBoolean(value) {
          return value === true || value === false || isObjectLike(value) && baseGetTag(value) == boolTag;
        }

        var isBuffer = nativeIsBuffer || stubFalse;
        var isDate = nodeIsDate ? baseUnary(nodeIsDate) : baseIsDate;

        function isElement(value) {
          return isObjectLike(value) && value.nodeType === 1 && !isPlainObject(value);
        }

        function isEmpty(value) {
          if (value == null) {
            return true;
          }
          if (isArrayLike(value) && (isArray(value) || typeof value == "string" || typeof value.splice == "function" || isBuffer(value) || isTypedArray(value) || isArguments(value))) {
            return !value.length;
          }
          var tag = getTag(value);
          if (tag == mapTag || tag == setTag) {
            return !value.size;
          }
          if (isPrototype(value)) {
            return !baseKeys(value).length;
          }
          for (var key in value) {
            if (hasOwnProperty.call(value, key)) {
              return false;
            }
          }
          return true;
        }

        function isEqual(value, other) {
          return baseIsEqual(value, other);
        }

        function isEqualWith(value, other, customizer) {
          customizer = typeof customizer == "function" ? customizer : undefined$1;
          var result2 = customizer ? customizer(value, other) : undefined$1;
          return result2 === undefined$1 ? baseIsEqual(value, other, undefined$1, customizer) : !!result2;
        }

        function isError(value) {
          if (!isObjectLike(value)) {
            return false;
          }
          var tag = baseGetTag(value);
          return tag == errorTag || tag == domExcTag || typeof value.message == "string" && typeof value.name == "string" && !isPlainObject(value);
        }

        function isFinite(value) {
          return typeof value == "number" && nativeIsFinite(value);
        }

        function isFunction(value) {
          if (!isObject(value)) {
            return false;
          }
          var tag = baseGetTag(value);
          return tag == funcTag || tag == genTag || tag == asyncTag || tag == proxyTag;
        }

        function isInteger(value) {
          return typeof value == "number" && value == toInteger(value);
        }

        function isLength(value) {
          return typeof value == "number" && value > -1 && value % 1 == 0 && value <= MAX_SAFE_INTEGER;
        }

        function isObject(value) {
          var type = typeof value;
          return value != null && (type == "object" || type == "function");
        }

        function isObjectLike(value) {
          return value != null && typeof value == "object";
        }

        var isMap = nodeIsMap ? baseUnary(nodeIsMap) : baseIsMap;

        function isMatch(object, source) {
          return object === source || baseIsMatch(object, source, getMatchData(source));
        }

        function isMatchWith(object, source, customizer) {
          customizer = typeof customizer == "function" ? customizer : undefined$1;
          return baseIsMatch(object, source, getMatchData(source), customizer);
        }

        function isNaN(value) {
          return isNumber(value) && value != +value;
        }

        function isNative(value) {
          if (isMaskable(value)) {
            throw new Error2(CORE_ERROR_TEXT);
          }
          return baseIsNative(value);
        }

        function isNull(value) {
          return value === null;
        }

        function isNil(value) {
          return value == null;
        }

        function isNumber(value) {
          return typeof value == "number" || isObjectLike(value) && baseGetTag(value) == numberTag;
        }

        function isPlainObject(value) {
          if (!isObjectLike(value) || baseGetTag(value) != objectTag) {
            return false;
          }
          var proto = getPrototype(value);
          if (proto === null) {
            return true;
          }
          var Ctor = hasOwnProperty.call(proto, "constructor") && proto.constructor;
          return typeof Ctor == "function" && Ctor instanceof Ctor && funcToString.call(Ctor) == objectCtorString;
        }

        var isRegExp = nodeIsRegExp ? baseUnary(nodeIsRegExp) : baseIsRegExp;

        function isSafeInteger(value) {
          return isInteger(value) && value >= -MAX_SAFE_INTEGER && value <= MAX_SAFE_INTEGER;
        }

        var isSet = nodeIsSet ? baseUnary(nodeIsSet) : baseIsSet;

        function isString(value) {
          return typeof value == "string" || !isArray(value) && isObjectLike(value) && baseGetTag(value) == stringTag;
        }

        function isSymbol(value) {
          return typeof value == "symbol" || isObjectLike(value) && baseGetTag(value) == symbolTag;
        }

        var isTypedArray = nodeIsTypedArray ? baseUnary(nodeIsTypedArray) : baseIsTypedArray;

        function isUndefined(value) {
          return value === undefined$1;
        }

        function isWeakMap(value) {
          return isObjectLike(value) && getTag(value) == weakMapTag;
        }

        function isWeakSet(value) {
          return isObjectLike(value) && baseGetTag(value) == weakSetTag;
        }

        var lt = createRelationalOperation(baseLt);
        var lte = createRelationalOperation(function (value, other) {
          return value <= other;
        });

        function toArray(value) {
          if (!value) {
            return [];
          }
          if (isArrayLike(value)) {
            return isString(value) ? stringToArray(value) : copyArray(value);
          }
          if (symIterator && value[symIterator]) {
            return iteratorToArray(value[symIterator]());
          }
          var tag = getTag(value), func = tag == mapTag ? mapToArray : tag == setTag ? setToArray : values;
          return func(value);
        }

        function toFinite(value) {
          if (!value) {
            return value === 0 ? value : 0;
          }
          value = toNumber(value);
          if (value === INFINITY || value === -INFINITY) {
            var sign = value < 0 ? -1 : 1;
            return sign * MAX_INTEGER;
          }
          return value === value ? value : 0;
        }

        function toInteger(value) {
          var result2 = toFinite(value), remainder = result2 % 1;
          return result2 === result2 ? remainder ? result2 - remainder : result2 : 0;
        }

        function toLength(value) {
          return value ? baseClamp(toInteger(value), 0, MAX_ARRAY_LENGTH) : 0;
        }

        function toNumber(value) {
          if (typeof value == "number") {
            return value;
          }
          if (isSymbol(value)) {
            return NAN;
          }
          if (isObject(value)) {
            var other = typeof value.valueOf == "function" ? value.valueOf() : value;
            value = isObject(other) ? other + "" : other;
          }
          if (typeof value != "string") {
            return value === 0 ? value : +value;
          }
          value = baseTrim(value);
          var isBinary = reIsBinary.test(value);
          return isBinary || reIsOctal.test(value) ? freeParseInt(value.slice(2), isBinary ? 2 : 8) : reIsBadHex.test(value) ? NAN : +value;
        }

        function toPlainObject(value) {
          return copyObject(value, keysIn(value));
        }

        function toSafeInteger(value) {
          return value ? baseClamp(toInteger(value), -MAX_SAFE_INTEGER, MAX_SAFE_INTEGER) : value === 0 ? value : 0;
        }

        function toString(value) {
          return value == null ? "" : baseToString(value);
        }

        var assign = createAssigner(function (object, source) {
          if (isPrototype(source) || isArrayLike(source)) {
            copyObject(source, keys(source), object);
            return;
          }
          for (var key in source) {
            if (hasOwnProperty.call(source, key)) {
              assignValue(object, key, source[key]);
            }
          }
        });
        var assignIn = createAssigner(function (object, source) {
          copyObject(source, keysIn(source), object);
        });
        var assignInWith = createAssigner(function (object, source, srcIndex, customizer) {
          copyObject(source, keysIn(source), object, customizer);
        });
        var assignWith = createAssigner(function (object, source, srcIndex, customizer) {
          copyObject(source, keys(source), object, customizer);
        });
        var at = flatRest(baseAt);

        function create(prototype, properties) {
          var result2 = baseCreate(prototype);
          return properties == null ? result2 : baseAssign(result2, properties);
        }

        var defaults = baseRest(function (object, sources) {
          object = Object2(object);
          var index = -1;
          var length = sources.length;
          var guard = length > 2 ? sources[2] : undefined$1;
          if (guard && isIterateeCall(sources[0], sources[1], guard)) {
            length = 1;
          }
          while (++index < length) {
            var source = sources[index];
            var props = keysIn(source);
            var propsIndex = -1;
            var propsLength = props.length;
            while (++propsIndex < propsLength) {
              var key = props[propsIndex];
              var value = object[key];
              if (value === undefined$1 || eq(value, objectProto[key]) && !hasOwnProperty.call(object, key)) {
                object[key] = source[key];
              }
            }
          }
          return object;
        });
        var defaultsDeep = baseRest(function (args) {
          args.push(undefined$1, customDefaultsMerge);
          return apply(mergeWith, undefined$1, args);
        });

        function findKey(object, predicate) {
          return baseFindKey(object, getIteratee(predicate, 3), baseForOwn);
        }

        function findLastKey(object, predicate) {
          return baseFindKey(object, getIteratee(predicate, 3), baseForOwnRight);
        }

        function forIn(object, iteratee2) {
          return object == null ? object : baseFor(object, getIteratee(iteratee2, 3), keysIn);
        }

        function forInRight(object, iteratee2) {
          return object == null ? object : baseForRight(object, getIteratee(iteratee2, 3), keysIn);
        }

        function forOwn(object, iteratee2) {
          return object && baseForOwn(object, getIteratee(iteratee2, 3));
        }

        function forOwnRight(object, iteratee2) {
          return object && baseForOwnRight(object, getIteratee(iteratee2, 3));
        }

        function functions(object) {
          return object == null ? [] : baseFunctions(object, keys(object));
        }

        function functionsIn(object) {
          return object == null ? [] : baseFunctions(object, keysIn(object));
        }

        function get(object, path, defaultValue) {
          var result2 = object == null ? undefined$1 : baseGet(object, path);
          return result2 === undefined$1 ? defaultValue : result2;
        }

        function has(object, path) {
          return object != null && hasPath(object, path, baseHas);
        }

        function hasIn(object, path) {
          return object != null && hasPath(object, path, baseHasIn);
        }

        var invert = createInverter(function (result2, value, key) {
          if (value != null && typeof value.toString != "function") {
            value = nativeObjectToString.call(value);
          }
          result2[value] = key;
        }, constant(identity));
        var invertBy = createInverter(function (result2, value, key) {
          if (value != null && typeof value.toString != "function") {
            value = nativeObjectToString.call(value);
          }
          if (hasOwnProperty.call(result2, value)) {
            result2[value].push(key);
          } else {
            result2[value] = [key];
          }
        }, getIteratee);
        var invoke = baseRest(baseInvoke);

        function keys(object) {
          return isArrayLike(object) ? arrayLikeKeys(object) : baseKeys(object);
        }

        function keysIn(object) {
          return isArrayLike(object) ? arrayLikeKeys(object, true) : baseKeysIn(object);
        }

        function mapKeys(object, iteratee2) {
          var result2 = {};
          iteratee2 = getIteratee(iteratee2, 3);
          baseForOwn(object, function (value, key, object2) {
            baseAssignValue(result2, iteratee2(value, key, object2), value);
          });
          return result2;
        }

        function mapValues(object, iteratee2) {
          var result2 = {};
          iteratee2 = getIteratee(iteratee2, 3);
          baseForOwn(object, function (value, key, object2) {
            baseAssignValue(result2, key, iteratee2(value, key, object2));
          });
          return result2;
        }

        var merge = createAssigner(function (object, source, srcIndex) {
          baseMerge(object, source, srcIndex);
        });
        var mergeWith = createAssigner(function (object, source, srcIndex, customizer) {
          baseMerge(object, source, srcIndex, customizer);
        });
        var omit = flatRest(function (object, paths) {
          var result2 = {};
          if (object == null) {
            return result2;
          }
          var isDeep = false;
          paths = arrayMap(paths, function (path) {
            path = castPath(path, object);
            isDeep || (isDeep = path.length > 1);
            return path;
          });
          copyObject(object, getAllKeysIn(object), result2);
          if (isDeep) {
            result2 = baseClone(result2, CLONE_DEEP_FLAG | CLONE_FLAT_FLAG | CLONE_SYMBOLS_FLAG, customOmitClone);
          }
          var length = paths.length;
          while (length--) {
            baseUnset(result2, paths[length]);
          }
          return result2;
        });

        function omitBy(object, predicate) {
          return pickBy(object, negate(getIteratee(predicate)));
        }

        var pick = flatRest(function (object, paths) {
          return object == null ? {} : basePick(object, paths);
        });

        function pickBy(object, predicate) {
          if (object == null) {
            return {};
          }
          var props = arrayMap(getAllKeysIn(object), function (prop) {
            return [prop];
          });
          predicate = getIteratee(predicate);
          return basePickBy(object, props, function (value, path) {
            return predicate(value, path[0]);
          });
        }

        function result(object, path, defaultValue) {
          path = castPath(path, object);
          var index = -1, length = path.length;
          if (!length) {
            length = 1;
            object = undefined$1;
          }
          while (++index < length) {
            var value = object == null ? undefined$1 : object[toKey(path[index])];
            if (value === undefined$1) {
              index = length;
              value = defaultValue;
            }
            object = isFunction(value) ? value.call(object) : value;
          }
          return object;
        }

        function set(object, path, value) {
          return object == null ? object : baseSet(object, path, value);
        }

        function setWith(object, path, value, customizer) {
          customizer = typeof customizer == "function" ? customizer : undefined$1;
          return object == null ? object : baseSet(object, path, value, customizer);
        }

        var toPairs = createToPairs(keys);
        var toPairsIn = createToPairs(keysIn);

        function transform(object, iteratee2, accumulator) {
          var isArr = isArray(object), isArrLike = isArr || isBuffer(object) || isTypedArray(object);
          iteratee2 = getIteratee(iteratee2, 4);
          if (accumulator == null) {
            var Ctor = object && object.constructor;
            if (isArrLike) {
              accumulator = isArr ? new Ctor() : [];
            } else if (isObject(object)) {
              accumulator = isFunction(Ctor) ? baseCreate(getPrototype(object)) : {};
            } else {
              accumulator = {};
            }
          }
          (isArrLike ? arrayEach : baseForOwn)(object, function (value, index, object2) {
            return iteratee2(accumulator, value, index, object2);
          });
          return accumulator;
        }

        function unset(object, path) {
          return object == null ? true : baseUnset(object, path);
        }

        function update(object, path, updater) {
          return object == null ? object : baseUpdate(object, path, castFunction(updater));
        }

        function updateWith(object, path, updater, customizer) {
          customizer = typeof customizer == "function" ? customizer : undefined$1;
          return object == null ? object : baseUpdate(object, path, castFunction(updater), customizer);
        }

        function values(object) {
          return object == null ? [] : baseValues(object, keys(object));
        }

        function valuesIn(object) {
          return object == null ? [] : baseValues(object, keysIn(object));
        }

        function clamp(number, lower, upper) {
          if (upper === undefined$1) {
            upper = lower;
            lower = undefined$1;
          }
          if (upper !== undefined$1) {
            upper = toNumber(upper);
            upper = upper === upper ? upper : 0;
          }
          if (lower !== undefined$1) {
            lower = toNumber(lower);
            lower = lower === lower ? lower : 0;
          }
          return baseClamp(toNumber(number), lower, upper);
        }

        function inRange(number, start, end) {
          start = toFinite(start);
          if (end === undefined$1) {
            end = start;
            start = 0;
          } else {
            end = toFinite(end);
          }
          number = toNumber(number);
          return baseInRange(number, start, end);
        }

        function random(lower, upper, floating) {
          if (floating && typeof floating != "boolean" && isIterateeCall(lower, upper, floating)) {
            upper = floating = undefined$1;
          }
          if (floating === undefined$1) {
            if (typeof upper == "boolean") {
              floating = upper;
              upper = undefined$1;
            } else if (typeof lower == "boolean") {
              floating = lower;
              lower = undefined$1;
            }
          }
          if (lower === undefined$1 && upper === undefined$1) {
            lower = 0;
            upper = 1;
          } else {
            lower = toFinite(lower);
            if (upper === undefined$1) {
              upper = lower;
              lower = 0;
            } else {
              upper = toFinite(upper);
            }
          }
          if (lower > upper) {
            var temp = lower;
            lower = upper;
            upper = temp;
          }
          if (floating || lower % 1 || upper % 1) {
            var rand = nativeRandom();
            return nativeMin(lower + rand * (upper - lower + freeParseFloat("1e-" + ((rand + "").length - 1))), upper);
          }
          return baseRandom(lower, upper);
        }

        var camelCase = createCompounder(function (result2, word, index) {
          word = word.toLowerCase();
          return result2 + (index ? capitalize(word) : word);
        });

        function capitalize(string) {
          return upperFirst(toString(string).toLowerCase());
        }

        function deburr(string) {
          string = toString(string);
          return string && string.replace(reLatin, deburrLetter).replace(reComboMark, "");
        }

        function endsWith(string, target, position) {
          string = toString(string);
          target = baseToString(target);
          var length = string.length;
          position = position === undefined$1 ? length : baseClamp(toInteger(position), 0, length);
          var end = position;
          position -= target.length;
          return position >= 0 && string.slice(position, end) == target;
        }

        function escape(string) {
          string = toString(string);
          return string && reHasUnescapedHtml.test(string) ? string.replace(reUnescapedHtml, escapeHtmlChar) : string;
        }

        function escapeRegExp(string) {
          string = toString(string);
          return string && reHasRegExpChar.test(string) ? string.replace(reRegExpChar, "\\$&") : string;
        }

        var kebabCase = createCompounder(function (result2, word, index) {
          return result2 + (index ? "-" : "") + word.toLowerCase();
        });
        var lowerCase = createCompounder(function (result2, word, index) {
          return result2 + (index ? " " : "") + word.toLowerCase();
        });
        var lowerFirst = createCaseFirst("toLowerCase");

        function pad(string, length, chars) {
          string = toString(string);
          length = toInteger(length);
          var strLength = length ? stringSize(string) : 0;
          if (!length || strLength >= length) {
            return string;
          }
          var mid = (length - strLength) / 2;
          return createPadding(nativeFloor(mid), chars) + string + createPadding(nativeCeil(mid), chars);
        }

        function padEnd(string, length, chars) {
          string = toString(string);
          length = toInteger(length);
          var strLength = length ? stringSize(string) : 0;
          return length && strLength < length ? string + createPadding(length - strLength, chars) : string;
        }

        function padStart(string, length, chars) {
          string = toString(string);
          length = toInteger(length);
          var strLength = length ? stringSize(string) : 0;
          return length && strLength < length ? createPadding(length - strLength, chars) + string : string;
        }

        function parseInt2(string, radix, guard) {
          if (guard || radix == null) {
            radix = 0;
          } else if (radix) {
            radix = +radix;
          }
          return nativeParseInt(toString(string).replace(reTrimStart, ""), radix || 0);
        }

        function repeat(string, n, guard) {
          if (guard ? isIterateeCall(string, n, guard) : n === undefined$1) {
            n = 1;
          } else {
            n = toInteger(n);
          }
          return baseRepeat(toString(string), n);
        }

        function replace() {
          var args = arguments, string = toString(args[0]);
          return args.length < 3 ? string : string.replace(args[1], args[2]);
        }

        var snakeCase = createCompounder(function (result2, word, index) {
          return result2 + (index ? "_" : "") + word.toLowerCase();
        });

        function split(string, separator, limit) {
          if (limit && typeof limit != "number" && isIterateeCall(string, separator, limit)) {
            separator = limit = undefined$1;
          }
          limit = limit === undefined$1 ? MAX_ARRAY_LENGTH : limit >>> 0;
          if (!limit) {
            return [];
          }
          string = toString(string);
          if (string && (typeof separator == "string" || separator != null && !isRegExp(separator))) {
            separator = baseToString(separator);
            if (!separator && hasUnicode(string)) {
              return castSlice(stringToArray(string), 0, limit);
            }
          }
          return string.split(separator, limit);
        }

        var startCase = createCompounder(function (result2, word, index) {
          return result2 + (index ? " " : "") + upperFirst(word);
        });

        function startsWith(string, target, position) {
          string = toString(string);
          position = position == null ? 0 : baseClamp(toInteger(position), 0, string.length);
          target = baseToString(target);
          return string.slice(position, position + target.length) == target;
        }

        function template(string, options, guard) {
          var settings = lodash2.templateSettings;
          if (guard && isIterateeCall(string, options, guard)) {
            options = undefined$1;
          }
          string = toString(string);
          options = assignInWith({}, options, settings, customDefaultsAssignIn);
          var imports = assignInWith({}, options.imports, settings.imports, customDefaultsAssignIn),
            importsKeys = keys(imports), importsValues = baseValues(imports, importsKeys);
          var isEscaping, isEvaluating, index = 0, interpolate = options.interpolate || reNoMatch, source = "__p += '";
          var reDelimiters = RegExp2(
            (options.escape || reNoMatch).source + "|" + interpolate.source + "|" + (interpolate === reInterpolate ? reEsTemplate : reNoMatch).source + "|" + (options.evaluate || reNoMatch).source + "|$",
            "g"
          );
          var sourceURL = "//# sourceURL=" + (hasOwnProperty.call(options, "sourceURL") ? (options.sourceURL + "").replace(/\s/g, " ") : "lodash.templateSources[" + ++templateCounter + "]") + "\n";
          string.replace(reDelimiters, function (match, escapeValue, interpolateValue, esTemplateValue, evaluateValue, offset) {
            interpolateValue || (interpolateValue = esTemplateValue);
            source += string.slice(index, offset).replace(reUnescapedString, escapeStringChar);
            if (escapeValue) {
              isEscaping = true;
              source += "' +\n__e(" + escapeValue + ") +\n'";
            }
            if (evaluateValue) {
              isEvaluating = true;
              source += "';\n" + evaluateValue + ";\n__p += '";
            }
            if (interpolateValue) {
              source += "' +\n((__t = (" + interpolateValue + ")) == null ? '' : __t) +\n'";
            }
            index = offset + match.length;
            return match;
          });
          source += "';\n";
          var variable = hasOwnProperty.call(options, "variable") && options.variable;
          if (!variable) {
            source = "with (obj) {\n" + source + "\n}\n";
          } else if (reForbiddenIdentifierChars.test(variable)) {
            throw new Error2(INVALID_TEMPL_VAR_ERROR_TEXT);
          }
          source = (isEvaluating ? source.replace(reEmptyStringLeading, "") : source).replace(reEmptyStringMiddle, "$1").replace(reEmptyStringTrailing, "$1;");
          source = "function(" + (variable || "obj") + ") {\n" + (variable ? "" : "obj || (obj = {});\n") + "var __t, __p = ''" + (isEscaping ? ", __e = _.escape" : "") + (isEvaluating ? ", __j = Array.prototype.join;\nfunction print() { __p += __j.call(arguments, '') }\n" : ";\n") + source + "return __p\n}";
          var result2 = attempt(function () {
            return Function2(importsKeys, sourceURL + "return " + source).apply(undefined$1, importsValues);
          });
          result2.source = source;
          if (isError(result2)) {
            throw result2;
          }
          return result2;
        }

        function toLower(value) {
          return toString(value).toLowerCase();
        }

        function toUpper(value) {
          return toString(value).toUpperCase();
        }

        function trim(string, chars, guard) {
          string = toString(string);
          if (string && (guard || chars === undefined$1)) {
            return baseTrim(string);
          }
          if (!string || !(chars = baseToString(chars))) {
            return string;
          }
          var strSymbols = stringToArray(string), chrSymbols = stringToArray(chars),
            start = charsStartIndex(strSymbols, chrSymbols), end = charsEndIndex(strSymbols, chrSymbols) + 1;
          return castSlice(strSymbols, start, end).join("");
        }

        function trimEnd(string, chars, guard) {
          string = toString(string);
          if (string && (guard || chars === undefined$1)) {
            return string.slice(0, trimmedEndIndex(string) + 1);
          }
          if (!string || !(chars = baseToString(chars))) {
            return string;
          }
          var strSymbols = stringToArray(string), end = charsEndIndex(strSymbols, stringToArray(chars)) + 1;
          return castSlice(strSymbols, 0, end).join("");
        }

        function trimStart(string, chars, guard) {
          string = toString(string);
          if (string && (guard || chars === undefined$1)) {
            return string.replace(reTrimStart, "");
          }
          if (!string || !(chars = baseToString(chars))) {
            return string;
          }
          var strSymbols = stringToArray(string), start = charsStartIndex(strSymbols, stringToArray(chars));
          return castSlice(strSymbols, start).join("");
        }

        function truncate(string, options) {
          var length = DEFAULT_TRUNC_LENGTH, omission = DEFAULT_TRUNC_OMISSION;
          if (isObject(options)) {
            var separator = "separator" in options ? options.separator : separator;
            length = "length" in options ? toInteger(options.length) : length;
            omission = "omission" in options ? baseToString(options.omission) : omission;
          }
          string = toString(string);
          var strLength = string.length;
          if (hasUnicode(string)) {
            var strSymbols = stringToArray(string);
            strLength = strSymbols.length;
          }
          if (length >= strLength) {
            return string;
          }
          var end = length - stringSize(omission);
          if (end < 1) {
            return omission;
          }
          var result2 = strSymbols ? castSlice(strSymbols, 0, end).join("") : string.slice(0, end);
          if (separator === undefined$1) {
            return result2 + omission;
          }
          if (strSymbols) {
            end += result2.length - end;
          }
          if (isRegExp(separator)) {
            if (string.slice(end).search(separator)) {
              var match, substring = result2;
              if (!separator.global) {
                separator = RegExp2(separator.source, toString(reFlags.exec(separator)) + "g");
              }
              separator.lastIndex = 0;
              while (match = separator.exec(substring)) {
                var newEnd = match.index;
              }
              result2 = result2.slice(0, newEnd === undefined$1 ? end : newEnd);
            }
          } else if (string.indexOf(baseToString(separator), end) != end) {
            var index = result2.lastIndexOf(separator);
            if (index > -1) {
              result2 = result2.slice(0, index);
            }
          }
          return result2 + omission;
        }

        function unescape(string) {
          string = toString(string);
          return string && reHasEscapedHtml.test(string) ? string.replace(reEscapedHtml, unescapeHtmlChar) : string;
        }

        var upperCase = createCompounder(function (result2, word, index) {
          return result2 + (index ? " " : "") + word.toUpperCase();
        });
        var upperFirst = createCaseFirst("toUpperCase");

        function words(string, pattern, guard) {
          string = toString(string);
          pattern = guard ? undefined$1 : pattern;
          if (pattern === undefined$1) {
            return hasUnicodeWord(string) ? unicodeWords(string) : asciiWords(string);
          }
          return string.match(pattern) || [];
        }

        var attempt = baseRest(function (func, args) {
          try {
            return apply(func, undefined$1, args);
          } catch (e) {
            return isError(e) ? e : new Error2(e);
          }
        });
        var bindAll = flatRest(function (object, methodNames) {
          arrayEach(methodNames, function (key) {
            key = toKey(key);
            baseAssignValue(object, key, bind(object[key], object));
          });
          return object;
        });

        function cond(pairs) {
          var length = pairs == null ? 0 : pairs.length, toIteratee = getIteratee();
          pairs = !length ? [] : arrayMap(pairs, function (pair) {
            if (typeof pair[1] != "function") {
              throw new TypeError2(FUNC_ERROR_TEXT);
            }
            return [toIteratee(pair[0]), pair[1]];
          });
          return baseRest(function (args) {
            var index = -1;
            while (++index < length) {
              var pair = pairs[index];
              if (apply(pair[0], this, args)) {
                return apply(pair[1], this, args);
              }
            }
          });
        }

        function conforms(source) {
          return baseConforms(baseClone(source, CLONE_DEEP_FLAG));
        }

        function constant(value) {
          return function () {
            return value;
          };
        }

        function defaultTo(value, defaultValue) {
          return value == null || value !== value ? defaultValue : value;
        }

        var flow = createFlow();
        var flowRight = createFlow(true);

        function identity(value) {
          return value;
        }

        function iteratee(func) {
          return baseIteratee(typeof func == "function" ? func : baseClone(func, CLONE_DEEP_FLAG));
        }

        function matches(source) {
          return baseMatches(baseClone(source, CLONE_DEEP_FLAG));
        }

        function matchesProperty(path, srcValue) {
          return baseMatchesProperty(path, baseClone(srcValue, CLONE_DEEP_FLAG));
        }

        var method = baseRest(function (path, args) {
          return function (object) {
            return baseInvoke(object, path, args);
          };
        });
        var methodOf = baseRest(function (object, args) {
          return function (path) {
            return baseInvoke(object, path, args);
          };
        });

        function mixin(object, source, options) {
          var props = keys(source), methodNames = baseFunctions(source, props);
          if (options == null && !(isObject(source) && (methodNames.length || !props.length))) {
            options = source;
            source = object;
            object = this;
            methodNames = baseFunctions(source, keys(source));
          }
          var chain2 = !(isObject(options) && "chain" in options) || !!options.chain, isFunc = isFunction(object);
          arrayEach(methodNames, function (methodName) {
            var func = source[methodName];
            object[methodName] = func;
            if (isFunc) {
              object.prototype[methodName] = function () {
                var chainAll = this.__chain__;
                if (chain2 || chainAll) {
                  var result2 = object(this.__wrapped__), actions = result2.__actions__ = copyArray(this.__actions__);
                  actions.push({"func": func, "args": arguments, "thisArg": object});
                  result2.__chain__ = chainAll;
                  return result2;
                }
                return func.apply(object, arrayPush([this.value()], arguments));
              };
            }
          });
          return object;
        }

        function noConflict() {
          if (root._ === this) {
            root._ = oldDash;
          }
          return this;
        }

        function noop() {
        }

        function nthArg(n) {
          n = toInteger(n);
          return baseRest(function (args) {
            return baseNth(args, n);
          });
        }

        var over = createOver(arrayMap);
        var overEvery = createOver(arrayEvery);
        var overSome = createOver(arraySome);

        function property(path) {
          return isKey(path) ? baseProperty(toKey(path)) : basePropertyDeep(path);
        }

        function propertyOf(object) {
          return function (path) {
            return object == null ? undefined$1 : baseGet(object, path);
          };
        }

        var range = createRange();
        var rangeRight = createRange(true);

        function stubArray() {
          return [];
        }

        function stubFalse() {
          return false;
        }

        function stubObject() {
          return {};
        }

        function stubString() {
          return "";
        }

        function stubTrue() {
          return true;
        }

        function times(n, iteratee2) {
          n = toInteger(n);
          if (n < 1 || n > MAX_SAFE_INTEGER) {
            return [];
          }
          var index = MAX_ARRAY_LENGTH, length = nativeMin(n, MAX_ARRAY_LENGTH);
          iteratee2 = getIteratee(iteratee2);
          n -= MAX_ARRAY_LENGTH;
          var result2 = baseTimes(length, iteratee2);
          while (++index < n) {
            iteratee2(index);
          }
          return result2;
        }

        function toPath(value) {
          if (isArray(value)) {
            return arrayMap(value, toKey);
          }
          return isSymbol(value) ? [value] : copyArray(stringToPath(toString(value)));
        }

        function uniqueId(prefix) {
          var id = ++idCounter;
          return toString(prefix) + id;
        }

        var add = createMathOperation(function (augend, addend) {
          return augend + addend;
        }, 0);
        var ceil = createRound("ceil");
        var divide = createMathOperation(function (dividend, divisor) {
          return dividend / divisor;
        }, 1);
        var floor = createRound("floor");

        function max(array) {
          return array && array.length ? baseExtremum(array, identity, baseGt) : undefined$1;
        }

        function maxBy(array, iteratee2) {
          return array && array.length ? baseExtremum(array, getIteratee(iteratee2, 2), baseGt) : undefined$1;
        }

        function mean(array) {
          return baseMean(array, identity);
        }

        function meanBy(array, iteratee2) {
          return baseMean(array, getIteratee(iteratee2, 2));
        }

        function min(array) {
          return array && array.length ? baseExtremum(array, identity, baseLt) : undefined$1;
        }

        function minBy(array, iteratee2) {
          return array && array.length ? baseExtremum(array, getIteratee(iteratee2, 2), baseLt) : undefined$1;
        }

        var multiply = createMathOperation(function (multiplier, multiplicand) {
          return multiplier * multiplicand;
        }, 1);
        var round = createRound("round");
        var subtract = createMathOperation(function (minuend, subtrahend) {
          return minuend - subtrahend;
        }, 0);

        function sum(array) {
          return array && array.length ? baseSum(array, identity) : 0;
        }

        function sumBy(array, iteratee2) {
          return array && array.length ? baseSum(array, getIteratee(iteratee2, 2)) : 0;
        }

        lodash2.after = after;
        lodash2.ary = ary;
        lodash2.assign = assign;
        lodash2.assignIn = assignIn;
        lodash2.assignInWith = assignInWith;
        lodash2.assignWith = assignWith;
        lodash2.at = at;
        lodash2.before = before;
        lodash2.bind = bind;
        lodash2.bindAll = bindAll;
        lodash2.bindKey = bindKey;
        lodash2.castArray = castArray;
        lodash2.chain = chain;
        lodash2.chunk = chunk;
        lodash2.compact = compact;
        lodash2.concat = concat;
        lodash2.cond = cond;
        lodash2.conforms = conforms;
        lodash2.constant = constant;
        lodash2.countBy = countBy;
        lodash2.create = create;
        lodash2.curry = curry;
        lodash2.curryRight = curryRight;
        lodash2.debounce = debounce;
        lodash2.defaults = defaults;
        lodash2.defaultsDeep = defaultsDeep;
        lodash2.defer = defer;
        lodash2.delay = delay;
        lodash2.difference = difference;
        lodash2.differenceBy = differenceBy;
        lodash2.differenceWith = differenceWith;
        lodash2.drop = drop;
        lodash2.dropRight = dropRight;
        lodash2.dropRightWhile = dropRightWhile;
        lodash2.dropWhile = dropWhile;
        lodash2.fill = fill;
        lodash2.filter = filter;
        lodash2.flatMap = flatMap;
        lodash2.flatMapDeep = flatMapDeep;
        lodash2.flatMapDepth = flatMapDepth;
        lodash2.flatten = flatten;
        lodash2.flattenDeep = flattenDeep;
        lodash2.flattenDepth = flattenDepth;
        lodash2.flip = flip;
        lodash2.flow = flow;
        lodash2.flowRight = flowRight;
        lodash2.fromPairs = fromPairs;
        lodash2.functions = functions;
        lodash2.functionsIn = functionsIn;
        lodash2.groupBy = groupBy;
        lodash2.initial = initial;
        lodash2.intersection = intersection;
        lodash2.intersectionBy = intersectionBy;
        lodash2.intersectionWith = intersectionWith;
        lodash2.invert = invert;
        lodash2.invertBy = invertBy;
        lodash2.invokeMap = invokeMap;
        lodash2.iteratee = iteratee;
        lodash2.keyBy = keyBy;
        lodash2.keys = keys;
        lodash2.keysIn = keysIn;
        lodash2.map = map;
        lodash2.mapKeys = mapKeys;
        lodash2.mapValues = mapValues;
        lodash2.matches = matches;
        lodash2.matchesProperty = matchesProperty;
        lodash2.memoize = memoize2;
        lodash2.merge = merge;
        lodash2.mergeWith = mergeWith;
        lodash2.method = method;
        lodash2.methodOf = methodOf;
        lodash2.mixin = mixin;
        lodash2.negate = negate;
        lodash2.nthArg = nthArg;
        lodash2.omit = omit;
        lodash2.omitBy = omitBy;
        lodash2.once = once;
        lodash2.orderBy = orderBy;
        lodash2.over = over;
        lodash2.overArgs = overArgs;
        lodash2.overEvery = overEvery;
        lodash2.overSome = overSome;
        lodash2.partial = partial;
        lodash2.partialRight = partialRight;
        lodash2.partition = partition;
        lodash2.pick = pick;
        lodash2.pickBy = pickBy;
        lodash2.property = property;
        lodash2.propertyOf = propertyOf;
        lodash2.pull = pull;
        lodash2.pullAll = pullAll;
        lodash2.pullAllBy = pullAllBy;
        lodash2.pullAllWith = pullAllWith;
        lodash2.pullAt = pullAt;
        lodash2.range = range;
        lodash2.rangeRight = rangeRight;
        lodash2.rearg = rearg;
        lodash2.reject = reject;
        lodash2.remove = remove;
        lodash2.rest = rest;
        lodash2.reverse = reverse;
        lodash2.sampleSize = sampleSize;
        lodash2.set = set;
        lodash2.setWith = setWith;
        lodash2.shuffle = shuffle;
        lodash2.slice = slice;
        lodash2.sortBy = sortBy;
        lodash2.sortedUniq = sortedUniq;
        lodash2.sortedUniqBy = sortedUniqBy;
        lodash2.split = split;
        lodash2.spread = spread;
        lodash2.tail = tail;
        lodash2.take = take;
        lodash2.takeRight = takeRight;
        lodash2.takeRightWhile = takeRightWhile;
        lodash2.takeWhile = takeWhile;
        lodash2.tap = tap;
        lodash2.throttle = throttle;
        lodash2.thru = thru;
        lodash2.toArray = toArray;
        lodash2.toPairs = toPairs;
        lodash2.toPairsIn = toPairsIn;
        lodash2.toPath = toPath;
        lodash2.toPlainObject = toPlainObject;
        lodash2.transform = transform;
        lodash2.unary = unary;
        lodash2.union = union;
        lodash2.unionBy = unionBy;
        lodash2.unionWith = unionWith;
        lodash2.uniq = uniq;
        lodash2.uniqBy = uniqBy;
        lodash2.uniqWith = uniqWith;
        lodash2.unset = unset;
        lodash2.unzip = unzip;
        lodash2.unzipWith = unzipWith;
        lodash2.update = update;
        lodash2.updateWith = updateWith;
        lodash2.values = values;
        lodash2.valuesIn = valuesIn;
        lodash2.without = without;
        lodash2.words = words;
        lodash2.wrap = wrap;
        lodash2.xor = xor;
        lodash2.xorBy = xorBy;
        lodash2.xorWith = xorWith;
        lodash2.zip = zip;
        lodash2.zipObject = zipObject;
        lodash2.zipObjectDeep = zipObjectDeep;
        lodash2.zipWith = zipWith;
        lodash2.entries = toPairs;
        lodash2.entriesIn = toPairsIn;
        lodash2.extend = assignIn;
        lodash2.extendWith = assignInWith;
        mixin(lodash2, lodash2);
        lodash2.add = add;
        lodash2.attempt = attempt;
        lodash2.camelCase = camelCase;
        lodash2.capitalize = capitalize;
        lodash2.ceil = ceil;
        lodash2.clamp = clamp;
        lodash2.clone = clone;
        lodash2.cloneDeep = cloneDeep;
        lodash2.cloneDeepWith = cloneDeepWith;
        lodash2.cloneWith = cloneWith;
        lodash2.conformsTo = conformsTo;
        lodash2.deburr = deburr;
        lodash2.defaultTo = defaultTo;
        lodash2.divide = divide;
        lodash2.endsWith = endsWith;
        lodash2.eq = eq;
        lodash2.escape = escape;
        lodash2.escapeRegExp = escapeRegExp;
        lodash2.every = every;
        lodash2.find = find;
        lodash2.findIndex = findIndex;
        lodash2.findKey = findKey;
        lodash2.findLast = findLast;
        lodash2.findLastIndex = findLastIndex;
        lodash2.findLastKey = findLastKey;
        lodash2.floor = floor;
        lodash2.forEach = forEach;
        lodash2.forEachRight = forEachRight;
        lodash2.forIn = forIn;
        lodash2.forInRight = forInRight;
        lodash2.forOwn = forOwn;
        lodash2.forOwnRight = forOwnRight;
        lodash2.get = get;
        lodash2.gt = gt;
        lodash2.gte = gte;
        lodash2.has = has;
        lodash2.hasIn = hasIn;
        lodash2.head = head;
        lodash2.identity = identity;
        lodash2.includes = includes;
        lodash2.indexOf = indexOf;
        lodash2.inRange = inRange;
        lodash2.invoke = invoke;
        lodash2.isArguments = isArguments;
        lodash2.isArray = isArray;
        lodash2.isArrayBuffer = isArrayBuffer;
        lodash2.isArrayLike = isArrayLike;
        lodash2.isArrayLikeObject = isArrayLikeObject;
        lodash2.isBoolean = isBoolean;
        lodash2.isBuffer = isBuffer;
        lodash2.isDate = isDate;
        lodash2.isElement = isElement;
        lodash2.isEmpty = isEmpty;
        lodash2.isEqual = isEqual;
        lodash2.isEqualWith = isEqualWith;
        lodash2.isError = isError;
        lodash2.isFinite = isFinite;
        lodash2.isFunction = isFunction;
        lodash2.isInteger = isInteger;
        lodash2.isLength = isLength;
        lodash2.isMap = isMap;
        lodash2.isMatch = isMatch;
        lodash2.isMatchWith = isMatchWith;
        lodash2.isNaN = isNaN;
        lodash2.isNative = isNative;
        lodash2.isNil = isNil;
        lodash2.isNull = isNull;
        lodash2.isNumber = isNumber;
        lodash2.isObject = isObject;
        lodash2.isObjectLike = isObjectLike;
        lodash2.isPlainObject = isPlainObject;
        lodash2.isRegExp = isRegExp;
        lodash2.isSafeInteger = isSafeInteger;
        lodash2.isSet = isSet;
        lodash2.isString = isString;
        lodash2.isSymbol = isSymbol;
        lodash2.isTypedArray = isTypedArray;
        lodash2.isUndefined = isUndefined;
        lodash2.isWeakMap = isWeakMap;
        lodash2.isWeakSet = isWeakSet;
        lodash2.join = join;
        lodash2.kebabCase = kebabCase;
        lodash2.last = last;
        lodash2.lastIndexOf = lastIndexOf;
        lodash2.lowerCase = lowerCase;
        lodash2.lowerFirst = lowerFirst;
        lodash2.lt = lt;
        lodash2.lte = lte;
        lodash2.max = max;
        lodash2.maxBy = maxBy;
        lodash2.mean = mean;
        lodash2.meanBy = meanBy;
        lodash2.min = min;
        lodash2.minBy = minBy;
        lodash2.stubArray = stubArray;
        lodash2.stubFalse = stubFalse;
        lodash2.stubObject = stubObject;
        lodash2.stubString = stubString;
        lodash2.stubTrue = stubTrue;
        lodash2.multiply = multiply;
        lodash2.nth = nth;
        lodash2.noConflict = noConflict;
        lodash2.noop = noop;
        lodash2.now = now;
        lodash2.pad = pad;
        lodash2.padEnd = padEnd;
        lodash2.padStart = padStart;
        lodash2.parseInt = parseInt2;
        lodash2.random = random;
        lodash2.reduce = reduce;
        lodash2.reduceRight = reduceRight;
        lodash2.repeat = repeat;
        lodash2.replace = replace;
        lodash2.result = result;
        lodash2.round = round;
        lodash2.runInContext = runInContext2;
        lodash2.sample = sample;
        lodash2.size = size;
        lodash2.snakeCase = snakeCase;
        lodash2.some = some;
        lodash2.sortedIndex = sortedIndex;
        lodash2.sortedIndexBy = sortedIndexBy;
        lodash2.sortedIndexOf = sortedIndexOf;
        lodash2.sortedLastIndex = sortedLastIndex;
        lodash2.sortedLastIndexBy = sortedLastIndexBy;
        lodash2.sortedLastIndexOf = sortedLastIndexOf;
        lodash2.startCase = startCase;
        lodash2.startsWith = startsWith;
        lodash2.subtract = subtract;
        lodash2.sum = sum;
        lodash2.sumBy = sumBy;
        lodash2.template = template;
        lodash2.times = times;
        lodash2.toFinite = toFinite;
        lodash2.toInteger = toInteger;
        lodash2.toLength = toLength;
        lodash2.toLower = toLower;
        lodash2.toNumber = toNumber;
        lodash2.toSafeInteger = toSafeInteger;
        lodash2.toString = toString;
        lodash2.toUpper = toUpper;
        lodash2.trim = trim;
        lodash2.trimEnd = trimEnd;
        lodash2.trimStart = trimStart;
        lodash2.truncate = truncate;
        lodash2.unescape = unescape;
        lodash2.uniqueId = uniqueId;
        lodash2.upperCase = upperCase;
        lodash2.upperFirst = upperFirst;
        lodash2.each = forEach;
        lodash2.eachRight = forEachRight;
        lodash2.first = head;
        mixin(lodash2, function () {
          var source = {};
          baseForOwn(lodash2, function (func, methodName) {
            if (!hasOwnProperty.call(lodash2.prototype, methodName)) {
              source[methodName] = func;
            }
          });
          return source;
        }(), {"chain": false});
        lodash2.VERSION = VERSION;
        arrayEach(["bind", "bindKey", "curry", "curryRight", "partial", "partialRight"], function (methodName) {
          lodash2[methodName].placeholder = lodash2;
        });
        arrayEach(["drop", "take"], function (methodName, index) {
          LazyWrapper.prototype[methodName] = function (n) {
            n = n === undefined$1 ? 1 : nativeMax(toInteger(n), 0);
            var result2 = this.__filtered__ && !index ? new LazyWrapper(this) : this.clone();
            if (result2.__filtered__) {
              result2.__takeCount__ = nativeMin(n, result2.__takeCount__);
            } else {
              result2.__views__.push({
                "size": nativeMin(n, MAX_ARRAY_LENGTH),
                "type": methodName + (result2.__dir__ < 0 ? "Right" : "")
              });
            }
            return result2;
          };
          LazyWrapper.prototype[methodName + "Right"] = function (n) {
            return this.reverse()[methodName](n).reverse();
          };
        });
        arrayEach(["filter", "map", "takeWhile"], function (methodName, index) {
          var type = index + 1, isFilter = type == LAZY_FILTER_FLAG || type == LAZY_WHILE_FLAG;
          LazyWrapper.prototype[methodName] = function (iteratee2) {
            var result2 = this.clone();
            result2.__iteratees__.push({
              "iteratee": getIteratee(iteratee2, 3),
              "type": type
            });
            result2.__filtered__ = result2.__filtered__ || isFilter;
            return result2;
          };
        });
        arrayEach(["head", "last"], function (methodName, index) {
          var takeName = "take" + (index ? "Right" : "");
          LazyWrapper.prototype[methodName] = function () {
            return this[takeName](1).value()[0];
          };
        });
        arrayEach(["initial", "tail"], function (methodName, index) {
          var dropName = "drop" + (index ? "" : "Right");
          LazyWrapper.prototype[methodName] = function () {
            return this.__filtered__ ? new LazyWrapper(this) : this[dropName](1);
          };
        });
        LazyWrapper.prototype.compact = function () {
          return this.filter(identity);
        };
        LazyWrapper.prototype.find = function (predicate) {
          return this.filter(predicate).head();
        };
        LazyWrapper.prototype.findLast = function (predicate) {
          return this.reverse().find(predicate);
        };
        LazyWrapper.prototype.invokeMap = baseRest(function (path, args) {
          if (typeof path == "function") {
            return new LazyWrapper(this);
          }
          return this.map(function (value) {
            return baseInvoke(value, path, args);
          });
        });
        LazyWrapper.prototype.reject = function (predicate) {
          return this.filter(negate(getIteratee(predicate)));
        };
        LazyWrapper.prototype.slice = function (start, end) {
          start = toInteger(start);
          var result2 = this;
          if (result2.__filtered__ && (start > 0 || end < 0)) {
            return new LazyWrapper(result2);
          }
          if (start < 0) {
            result2 = result2.takeRight(-start);
          } else if (start) {
            result2 = result2.drop(start);
          }
          if (end !== undefined$1) {
            end = toInteger(end);
            result2 = end < 0 ? result2.dropRight(-end) : result2.take(end - start);
          }
          return result2;
        };
        LazyWrapper.prototype.takeRightWhile = function (predicate) {
          return this.reverse().takeWhile(predicate).reverse();
        };
        LazyWrapper.prototype.toArray = function () {
          return this.take(MAX_ARRAY_LENGTH);
        };
        baseForOwn(LazyWrapper.prototype, function (func, methodName) {
          var checkIteratee = /^(?:filter|find|map|reject)|While$/.test(methodName),
            isTaker = /^(?:head|last)$/.test(methodName),
            lodashFunc = lodash2[isTaker ? "take" + (methodName == "last" ? "Right" : "") : methodName],
            retUnwrapped = isTaker || /^find/.test(methodName);
          if (!lodashFunc) {
            return;
          }
          lodash2.prototype[methodName] = function () {
            var value = this.__wrapped__, args = isTaker ? [1] : arguments, isLazy = value instanceof LazyWrapper,
              iteratee2 = args[0], useLazy = isLazy || isArray(value);
            var interceptor = function (value2) {
              var result3 = lodashFunc.apply(lodash2, arrayPush([value2], args));
              return isTaker && chainAll ? result3[0] : result3;
            };
            if (useLazy && checkIteratee && typeof iteratee2 == "function" && iteratee2.length != 1) {
              isLazy = useLazy = false;
            }
            var chainAll = this.__chain__, isHybrid = !!this.__actions__.length,
              isUnwrapped = retUnwrapped && !chainAll, onlyLazy = isLazy && !isHybrid;
            if (!retUnwrapped && useLazy) {
              value = onlyLazy ? value : new LazyWrapper(this);
              var result2 = func.apply(value, args);
              result2.__actions__.push({"func": thru, "args": [interceptor], "thisArg": undefined$1});
              return new LodashWrapper(result2, chainAll);
            }
            if (isUnwrapped && onlyLazy) {
              return func.apply(this, args);
            }
            result2 = this.thru(interceptor);
            return isUnwrapped ? isTaker ? result2.value()[0] : result2.value() : result2;
          };
        });
        arrayEach(["pop", "push", "shift", "sort", "splice", "unshift"], function (methodName) {
          var func = arrayProto[methodName], chainName = /^(?:push|sort|unshift)$/.test(methodName) ? "tap" : "thru",
            retUnwrapped = /^(?:pop|shift)$/.test(methodName);
          lodash2.prototype[methodName] = function () {
            var args = arguments;
            if (retUnwrapped && !this.__chain__) {
              var value = this.value();
              return func.apply(isArray(value) ? value : [], args);
            }
            return this[chainName](function (value2) {
              return func.apply(isArray(value2) ? value2 : [], args);
            });
          };
        });
        baseForOwn(LazyWrapper.prototype, function (func, methodName) {
          var lodashFunc = lodash2[methodName];
          if (lodashFunc) {
            var key = lodashFunc.name + "";
            if (!hasOwnProperty.call(realNames, key)) {
              realNames[key] = [];
            }
            realNames[key].push({"name": methodName, "func": lodashFunc});
          }
        });
        realNames[createHybrid(undefined$1, WRAP_BIND_KEY_FLAG).name] = [{
          "name": "wrapper",
          "func": undefined$1
        }];
        LazyWrapper.prototype.clone = lazyClone;
        LazyWrapper.prototype.reverse = lazyReverse;
        LazyWrapper.prototype.value = lazyValue;
        lodash2.prototype.at = wrapperAt;
        lodash2.prototype.chain = wrapperChain;
        lodash2.prototype.commit = wrapperCommit;
        lodash2.prototype.next = wrapperNext;
        lodash2.prototype.plant = wrapperPlant;
        lodash2.prototype.reverse = wrapperReverse;
        lodash2.prototype.toJSON = lodash2.prototype.valueOf = lodash2.prototype.value = wrapperValue;
        lodash2.prototype.first = lodash2.prototype.head;
        if (symIterator) {
          lodash2.prototype[symIterator] = wrapperToIterator;
        }
        return lodash2;
      };
      var _2 = runInContext();
      if (freeModule) {
        (freeModule.exports = _2)._ = _2;
        freeExports._ = _2;
      } else {
        root._ = _2;
      }
    }).call(commonjsGlobal);
  })(lodash, lodash.exports);
  var jsxRuntime = {exports: {}};
  var reactJsxRuntime_development = {};
  /**
   * @license React
   * react-jsx-runtime.development.js
   *
   * Copyright (c) Facebook, Inc. and its affiliates.
   *
   * This source code is licensed under the MIT license found in the
   * LICENSE file in the root directory of this source tree.
   */
  {
    (function () {
      var React2 = window["React"];
      var enableScopeAPI = false;
      var enableCacheElement = false;
      var enableTransitionTracing = false;
      var enableLegacyHidden = false;
      var enableDebugTracing = false;
      var REACT_ELEMENT_TYPE = Symbol.for("react.element");
      var REACT_PORTAL_TYPE = Symbol.for("react.portal");
      var REACT_FRAGMENT_TYPE = Symbol.for("react.fragment");
      var REACT_STRICT_MODE_TYPE = Symbol.for("react.strict_mode");
      var REACT_PROFILER_TYPE = Symbol.for("react.profiler");
      var REACT_PROVIDER_TYPE = Symbol.for("react.provider");
      var REACT_CONTEXT_TYPE = Symbol.for("react.context");
      var REACT_FORWARD_REF_TYPE = Symbol.for("react.forward_ref");
      var REACT_SUSPENSE_TYPE = Symbol.for("react.suspense");
      var REACT_SUSPENSE_LIST_TYPE = Symbol.for("react.suspense_list");
      var REACT_MEMO_TYPE = Symbol.for("react.memo");
      var REACT_LAZY_TYPE = Symbol.for("react.lazy");
      var REACT_OFFSCREEN_TYPE = Symbol.for("react.offscreen");
      var MAYBE_ITERATOR_SYMBOL = Symbol.iterator;
      var FAUX_ITERATOR_SYMBOL = "@@iterator";

      function getIteratorFn(maybeIterable) {
        if (maybeIterable === null || typeof maybeIterable !== "object") {
          return null;
        }
        var maybeIterator = MAYBE_ITERATOR_SYMBOL && maybeIterable[MAYBE_ITERATOR_SYMBOL] || maybeIterable[FAUX_ITERATOR_SYMBOL];
        if (typeof maybeIterator === "function") {
          return maybeIterator;
        }
        return null;
      }

      var ReactSharedInternals = React2.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED;

      function error(format) {
        {
          {
            for (var _len2 = arguments.length, args = new Array(_len2 > 1 ? _len2 - 1 : 0), _key2 = 1; _key2 < _len2; _key2++) {
              args[_key2 - 1] = arguments[_key2];
            }
            printWarning("error", format, args);
          }
        }
      }

      function printWarning(level, format, args) {
        {
          var ReactDebugCurrentFrame2 = ReactSharedInternals.ReactDebugCurrentFrame;
          var stack = ReactDebugCurrentFrame2.getStackAddendum();
          if (stack !== "") {
            format += "%s";
            args = args.concat([stack]);
          }
          var argsWithFormat = args.map(function (item) {
            return String(item);
          });
          argsWithFormat.unshift("Warning: " + format);
          Function.prototype.apply.call(console[level], console, argsWithFormat);
        }
      }

      var REACT_MODULE_REFERENCE;
      {
        REACT_MODULE_REFERENCE = Symbol.for("react.module.reference");
      }

      function isValidElementType(type) {
        if (typeof type === "string" || typeof type === "function") {
          return true;
        }
        if (type === REACT_FRAGMENT_TYPE || type === REACT_PROFILER_TYPE || enableDebugTracing || type === REACT_STRICT_MODE_TYPE || type === REACT_SUSPENSE_TYPE || type === REACT_SUSPENSE_LIST_TYPE || enableLegacyHidden || type === REACT_OFFSCREEN_TYPE || enableScopeAPI || enableCacheElement || enableTransitionTracing) {
          return true;
        }
        if (typeof type === "object" && type !== null) {
          if (type.$$typeof === REACT_LAZY_TYPE || type.$$typeof === REACT_MEMO_TYPE || type.$$typeof === REACT_PROVIDER_TYPE || type.$$typeof === REACT_CONTEXT_TYPE || type.$$typeof === REACT_FORWARD_REF_TYPE || type.$$typeof === REACT_MODULE_REFERENCE || type.getModuleId !== void 0) {
            return true;
          }
        }
        return false;
      }

      function getWrappedName(outerType, innerType, wrapperName) {
        var displayName = outerType.displayName;
        if (displayName) {
          return displayName;
        }
        var functionName = innerType.displayName || innerType.name || "";
        return functionName !== "" ? wrapperName + "(" + functionName + ")" : wrapperName;
      }

      function getContextName(type) {
        return type.displayName || "Context";
      }

      function getComponentNameFromType(type) {
        if (type == null) {
          return null;
        }
        {
          if (typeof type.tag === "number") {
            error("Received an unexpected object in getComponentNameFromType(). This is likely a bug in React. Please file an issue.");
          }
        }
        if (typeof type === "function") {
          return type.displayName || type.name || null;
        }
        if (typeof type === "string") {
          return type;
        }
        switch (type) {
          case REACT_FRAGMENT_TYPE:
            return "Fragment";
          case REACT_PORTAL_TYPE:
            return "Portal";
          case REACT_PROFILER_TYPE:
            return "Profiler";
          case REACT_STRICT_MODE_TYPE:
            return "StrictMode";
          case REACT_SUSPENSE_TYPE:
            return "Suspense";
          case REACT_SUSPENSE_LIST_TYPE:
            return "SuspenseList";
        }
        if (typeof type === "object") {
          switch (type.$$typeof) {
            case REACT_CONTEXT_TYPE:
              var context = type;
              return getContextName(context) + ".Consumer";
            case REACT_PROVIDER_TYPE:
              var provider = type;
              return getContextName(provider._context) + ".Provider";
            case REACT_FORWARD_REF_TYPE:
              return getWrappedName(type, type.render, "ForwardRef");
            case REACT_MEMO_TYPE:
              var outerName = type.displayName || null;
              if (outerName !== null) {
                return outerName;
              }
              return getComponentNameFromType(type.type) || "Memo";
            case REACT_LAZY_TYPE: {
              var lazyComponent = type;
              var payload = lazyComponent._payload;
              var init = lazyComponent._init;
              try {
                return getComponentNameFromType(init(payload));
              } catch (x2) {
                return null;
              }
            }
          }
        }
        return null;
      }

      var assign = Object.assign;
      var disabledDepth = 0;
      var prevLog;
      var prevInfo;
      var prevWarn;
      var prevError;
      var prevGroup;
      var prevGroupCollapsed;
      var prevGroupEnd;

      function disabledLog() {
      }

      disabledLog.__reactDisabledLog = true;

      function disableLogs() {
        {
          if (disabledDepth === 0) {
            prevLog = console.log;
            prevInfo = console.info;
            prevWarn = console.warn;
            prevError = console.error;
            prevGroup = console.group;
            prevGroupCollapsed = console.groupCollapsed;
            prevGroupEnd = console.groupEnd;
            var props = {
              configurable: true,
              enumerable: true,
              value: disabledLog,
              writable: true
            };
            Object.defineProperties(console, {
              info: props,
              log: props,
              warn: props,
              error: props,
              group: props,
              groupCollapsed: props,
              groupEnd: props
            });
          }
          disabledDepth++;
        }
      }

      function reenableLogs() {
        {
          disabledDepth--;
          if (disabledDepth === 0) {
            var props = {
              configurable: true,
              enumerable: true,
              writable: true
            };
            Object.defineProperties(console, {
              log: assign({}, props, {
                value: prevLog
              }),
              info: assign({}, props, {
                value: prevInfo
              }),
              warn: assign({}, props, {
                value: prevWarn
              }),
              error: assign({}, props, {
                value: prevError
              }),
              group: assign({}, props, {
                value: prevGroup
              }),
              groupCollapsed: assign({}, props, {
                value: prevGroupCollapsed
              }),
              groupEnd: assign({}, props, {
                value: prevGroupEnd
              })
            });
          }
          if (disabledDepth < 0) {
            error("disabledDepth fell below zero. This is a bug in React. Please file an issue.");
          }
        }
      }

      var ReactCurrentDispatcher = ReactSharedInternals.ReactCurrentDispatcher;
      var prefix;

      function describeBuiltInComponentFrame(name, source, ownerFn) {
        {
          if (prefix === void 0) {
            try {
              throw Error();
            } catch (x2) {
              var match = x2.stack.trim().match(/\n( *(at )?)/);
              prefix = match && match[1] || "";
            }
          }
          return "\n" + prefix + name;
        }
      }

      var reentry = false;
      var componentFrameCache;
      {
        var PossiblyWeakMap = typeof WeakMap === "function" ? WeakMap : Map;
        componentFrameCache = new PossiblyWeakMap();
      }

      function describeNativeComponentFrame(fn, construct) {
        if (!fn || reentry) {
          return "";
        }
        {
          var frame = componentFrameCache.get(fn);
          if (frame !== void 0) {
            return frame;
          }
        }
        var control;
        reentry = true;
        var previousPrepareStackTrace = Error.prepareStackTrace;
        Error.prepareStackTrace = void 0;
        var previousDispatcher;
        {
          previousDispatcher = ReactCurrentDispatcher.current;
          ReactCurrentDispatcher.current = null;
          disableLogs();
        }
        try {
          if (construct) {
            var Fake = function () {
              throw Error();
            };
            Object.defineProperty(Fake.prototype, "props", {
              set: function () {
                throw Error();
              }
            });
            if (typeof Reflect === "object" && Reflect.construct) {
              try {
                Reflect.construct(Fake, []);
              } catch (x2) {
                control = x2;
              }
              Reflect.construct(fn, [], Fake);
            } else {
              try {
                Fake.call();
              } catch (x2) {
                control = x2;
              }
              fn.call(Fake.prototype);
            }
          } else {
            try {
              throw Error();
            } catch (x2) {
              control = x2;
            }
            fn();
          }
        } catch (sample) {
          if (sample && control && typeof sample.stack === "string") {
            var sampleLines = sample.stack.split("\n");
            var controlLines = control.stack.split("\n");
            var s2 = sampleLines.length - 1;
            var c2 = controlLines.length - 1;
            while (s2 >= 1 && c2 >= 0 && sampleLines[s2] !== controlLines[c2]) {
              c2--;
            }
            for (; s2 >= 1 && c2 >= 0; s2--, c2--) {
              if (sampleLines[s2] !== controlLines[c2]) {
                if (s2 !== 1 || c2 !== 1) {
                  do {
                    s2--;
                    c2--;
                    if (c2 < 0 || sampleLines[s2] !== controlLines[c2]) {
                      var _frame = "\n" + sampleLines[s2].replace(" at new ", " at ");
                      if (fn.displayName && _frame.includes("<anonymous>")) {
                        _frame = _frame.replace("<anonymous>", fn.displayName);
                      }
                      {
                        if (typeof fn === "function") {
                          componentFrameCache.set(fn, _frame);
                        }
                      }
                      return _frame;
                    }
                  } while (s2 >= 1 && c2 >= 0);
                }
                break;
              }
            }
          }
        } finally {
          reentry = false;
          {
            ReactCurrentDispatcher.current = previousDispatcher;
            reenableLogs();
          }
          Error.prepareStackTrace = previousPrepareStackTrace;
        }
        var name = fn ? fn.displayName || fn.name : "";
        var syntheticFrame = name ? describeBuiltInComponentFrame(name) : "";
        {
          if (typeof fn === "function") {
            componentFrameCache.set(fn, syntheticFrame);
          }
        }
        return syntheticFrame;
      }

      function describeFunctionComponentFrame(fn, source, ownerFn) {
        {
          return describeNativeComponentFrame(fn, false);
        }
      }

      function shouldConstruct(Component) {
        var prototype = Component.prototype;
        return !!(prototype && prototype.isReactComponent);
      }

      function describeUnknownElementTypeFrameInDEV(type, source, ownerFn) {
        if (type == null) {
          return "";
        }
        if (typeof type === "function") {
          {
            return describeNativeComponentFrame(type, shouldConstruct(type));
          }
        }
        if (typeof type === "string") {
          return describeBuiltInComponentFrame(type);
        }
        switch (type) {
          case REACT_SUSPENSE_TYPE:
            return describeBuiltInComponentFrame("Suspense");
          case REACT_SUSPENSE_LIST_TYPE:
            return describeBuiltInComponentFrame("SuspenseList");
        }
        if (typeof type === "object") {
          switch (type.$$typeof) {
            case REACT_FORWARD_REF_TYPE:
              return describeFunctionComponentFrame(type.render);
            case REACT_MEMO_TYPE:
              return describeUnknownElementTypeFrameInDEV(type.type, source, ownerFn);
            case REACT_LAZY_TYPE: {
              var lazyComponent = type;
              var payload = lazyComponent._payload;
              var init = lazyComponent._init;
              try {
                return describeUnknownElementTypeFrameInDEV(init(payload), source, ownerFn);
              } catch (x2) {
              }
            }
          }
        }
        return "";
      }

      var hasOwnProperty = Object.prototype.hasOwnProperty;
      var loggedTypeFailures = {};
      var ReactDebugCurrentFrame = ReactSharedInternals.ReactDebugCurrentFrame;

      function setCurrentlyValidatingElement(element) {
        {
          if (element) {
            var owner = element._owner;
            var stack = describeUnknownElementTypeFrameInDEV(element.type, element._source, owner ? owner.type : null);
            ReactDebugCurrentFrame.setExtraStackFrame(stack);
          } else {
            ReactDebugCurrentFrame.setExtraStackFrame(null);
          }
        }
      }

      function checkPropTypes(typeSpecs, values, location, componentName, element) {
        {
          var has = Function.call.bind(hasOwnProperty);
          for (var typeSpecName in typeSpecs) {
            if (has(typeSpecs, typeSpecName)) {
              var error$1 = void 0;
              try {
                if (typeof typeSpecs[typeSpecName] !== "function") {
                  var err = Error((componentName || "React class") + ": " + location + " type `" + typeSpecName + "` is invalid; it must be a function, usually from the `prop-types` package, but received `" + typeof typeSpecs[typeSpecName] + "`.This often happens because of typos such as `PropTypes.function` instead of `PropTypes.func`.");
                  err.name = "Invariant Violation";
                  throw err;
                }
                error$1 = typeSpecs[typeSpecName](values, typeSpecName, componentName, location, null, "SECRET_DO_NOT_PASS_THIS_OR_YOU_WILL_BE_FIRED");
              } catch (ex) {
                error$1 = ex;
              }
              if (error$1 && !(error$1 instanceof Error)) {
                setCurrentlyValidatingElement(element);
                error("%s: type specification of %s `%s` is invalid; the type checker function must return `null` or an `Error` but returned a %s. You may have forgotten to pass an argument to the type checker creator (arrayOf, instanceOf, objectOf, oneOf, oneOfType, and shape all require an argument).", componentName || "React class", location, typeSpecName, typeof error$1);
                setCurrentlyValidatingElement(null);
              }
              if (error$1 instanceof Error && !(error$1.message in loggedTypeFailures)) {
                loggedTypeFailures[error$1.message] = true;
                setCurrentlyValidatingElement(element);
                error("Failed %s type: %s", location, error$1.message);
                setCurrentlyValidatingElement(null);
              }
            }
          }
        }
      }

      var isArrayImpl = Array.isArray;

      function isArray(a) {
        return isArrayImpl(a);
      }

      function typeName(value) {
        {
          var hasToStringTag = typeof Symbol === "function" && Symbol.toStringTag;
          var type = hasToStringTag && value[Symbol.toStringTag] || value.constructor.name || "Object";
          return type;
        }
      }

      function willCoercionThrow(value) {
        {
          try {
            testStringCoercion(value);
            return false;
          } catch (e) {
            return true;
          }
        }
      }

      function testStringCoercion(value) {
        return "" + value;
      }

      function checkKeyStringCoercion(value) {
        {
          if (willCoercionThrow(value)) {
            error("The provided key is an unsupported type %s. This value must be coerced to a string before before using it here.", typeName(value));
            return testStringCoercion(value);
          }
        }
      }

      var ReactCurrentOwner = ReactSharedInternals.ReactCurrentOwner;
      var RESERVED_PROPS = {
        key: true,
        ref: true,
        __self: true,
        __source: true
      };
      var specialPropKeyWarningShown;
      var specialPropRefWarningShown;
      var didWarnAboutStringRefs;
      {
        didWarnAboutStringRefs = {};
      }

      function hasValidRef(config) {
        {
          if (hasOwnProperty.call(config, "ref")) {
            var getter = Object.getOwnPropertyDescriptor(config, "ref").get;
            if (getter && getter.isReactWarning) {
              return false;
            }
          }
        }
        return config.ref !== void 0;
      }

      function hasValidKey(config) {
        {
          if (hasOwnProperty.call(config, "key")) {
            var getter = Object.getOwnPropertyDescriptor(config, "key").get;
            if (getter && getter.isReactWarning) {
              return false;
            }
          }
        }
        return config.key !== void 0;
      }

      function warnIfStringRefCannotBeAutoConverted(config, self2) {
        {
          if (typeof config.ref === "string" && ReactCurrentOwner.current && self2 && ReactCurrentOwner.current.stateNode !== self2) {
            var componentName = getComponentNameFromType(ReactCurrentOwner.current.type);
            if (!didWarnAboutStringRefs[componentName]) {
              error('Component "%s" contains the string ref "%s". Support for string refs will be removed in a future major release. This case cannot be automatically converted to an arrow function. We ask you to manually fix this case by using useRef() or createRef() instead. Learn more about using refs safely here: https://reactjs.org/link/strict-mode-string-ref', getComponentNameFromType(ReactCurrentOwner.current.type), config.ref);
              didWarnAboutStringRefs[componentName] = true;
            }
          }
        }
      }

      function defineKeyPropWarningGetter(props, displayName) {
        {
          var warnAboutAccessingKey = function () {
            if (!specialPropKeyWarningShown) {
              specialPropKeyWarningShown = true;
              error("%s: `key` is not a prop. Trying to access it will result in `undefined` being returned. If you need to access the same value within the child component, you should pass it as a different prop. (https://reactjs.org/link/special-props)", displayName);
            }
          };
          warnAboutAccessingKey.isReactWarning = true;
          Object.defineProperty(props, "key", {
            get: warnAboutAccessingKey,
            configurable: true
          });
        }
      }

      function defineRefPropWarningGetter(props, displayName) {
        {
          var warnAboutAccessingRef = function () {
            if (!specialPropRefWarningShown) {
              specialPropRefWarningShown = true;
              error("%s: `ref` is not a prop. Trying to access it will result in `undefined` being returned. If you need to access the same value within the child component, you should pass it as a different prop. (https://reactjs.org/link/special-props)", displayName);
            }
          };
          warnAboutAccessingRef.isReactWarning = true;
          Object.defineProperty(props, "ref", {
            get: warnAboutAccessingRef,
            configurable: true
          });
        }
      }

      var ReactElement = function (type, key, ref, self2, source, owner, props) {
        var element = {
          $$typeof: REACT_ELEMENT_TYPE,
          type,
          key,
          ref,
          props,
          _owner: owner
        };
        {
          element._store = {};
          Object.defineProperty(element._store, "validated", {
            configurable: false,
            enumerable: false,
            writable: true,
            value: false
          });
          Object.defineProperty(element, "_self", {
            configurable: false,
            enumerable: false,
            writable: false,
            value: self2
          });
          Object.defineProperty(element, "_source", {
            configurable: false,
            enumerable: false,
            writable: false,
            value: source
          });
          if (Object.freeze) {
            Object.freeze(element.props);
            Object.freeze(element);
          }
        }
        return element;
      };

      function jsxDEV(type, config, maybeKey, source, self2) {
        {
          var propName;
          var props = {};
          var key = null;
          var ref = null;
          if (maybeKey !== void 0) {
            {
              checkKeyStringCoercion(maybeKey);
            }
            key = "" + maybeKey;
          }
          if (hasValidKey(config)) {
            {
              checkKeyStringCoercion(config.key);
            }
            key = "" + config.key;
          }
          if (hasValidRef(config)) {
            ref = config.ref;
            warnIfStringRefCannotBeAutoConverted(config, self2);
          }
          for (propName in config) {
            if (hasOwnProperty.call(config, propName) && !RESERVED_PROPS.hasOwnProperty(propName)) {
              props[propName] = config[propName];
            }
          }
          if (type && type.defaultProps) {
            var defaultProps = type.defaultProps;
            for (propName in defaultProps) {
              if (props[propName] === void 0) {
                props[propName] = defaultProps[propName];
              }
            }
          }
          if (key || ref) {
            var displayName = typeof type === "function" ? type.displayName || type.name || "Unknown" : type;
            if (key) {
              defineKeyPropWarningGetter(props, displayName);
            }
            if (ref) {
              defineRefPropWarningGetter(props, displayName);
            }
          }
          return ReactElement(type, key, ref, self2, source, ReactCurrentOwner.current, props);
        }
      }

      var ReactCurrentOwner$1 = ReactSharedInternals.ReactCurrentOwner;
      var ReactDebugCurrentFrame$1 = ReactSharedInternals.ReactDebugCurrentFrame;

      function setCurrentlyValidatingElement$1(element) {
        {
          if (element) {
            var owner = element._owner;
            var stack = describeUnknownElementTypeFrameInDEV(element.type, element._source, owner ? owner.type : null);
            ReactDebugCurrentFrame$1.setExtraStackFrame(stack);
          } else {
            ReactDebugCurrentFrame$1.setExtraStackFrame(null);
          }
        }
      }

      var propTypesMisspellWarningShown;
      {
        propTypesMisspellWarningShown = false;
      }

      function isValidElement(object) {
        {
          return typeof object === "object" && object !== null && object.$$typeof === REACT_ELEMENT_TYPE;
        }
      }

      function getDeclarationErrorAddendum() {
        {
          if (ReactCurrentOwner$1.current) {
            var name = getComponentNameFromType(ReactCurrentOwner$1.current.type);
            if (name) {
              return "\n\nCheck the render method of `" + name + "`.";
            }
          }
          return "";
        }
      }

      function getSourceInfoErrorAddendum(source) {
        {
          if (source !== void 0) {
            var fileName = source.fileName.replace(/^.*[\\\/]/, "");
            var lineNumber = source.lineNumber;
            return "\n\nCheck your code at " + fileName + ":" + lineNumber + ".";
          }
          return "";
        }
      }

      var ownerHasKeyUseWarning = {};

      function getCurrentComponentErrorInfo(parentType) {
        {
          var info = getDeclarationErrorAddendum();
          if (!info) {
            var parentName = typeof parentType === "string" ? parentType : parentType.displayName || parentType.name;
            if (parentName) {
              info = "\n\nCheck the top-level render call using <" + parentName + ">.";
            }
          }
          return info;
        }
      }

      function validateExplicitKey(element, parentType) {
        {
          if (!element._store || element._store.validated || element.key != null) {
            return;
          }
          element._store.validated = true;
          var currentComponentErrorInfo = getCurrentComponentErrorInfo(parentType);
          if (ownerHasKeyUseWarning[currentComponentErrorInfo]) {
            return;
          }
          ownerHasKeyUseWarning[currentComponentErrorInfo] = true;
          var childOwner = "";
          if (element && element._owner && element._owner !== ReactCurrentOwner$1.current) {
            childOwner = " It was passed a child from " + getComponentNameFromType(element._owner.type) + ".";
          }
          setCurrentlyValidatingElement$1(element);
          error('Each child in a list should have a unique "key" prop.%s%s See https://reactjs.org/link/warning-keys for more information.', currentComponentErrorInfo, childOwner);
          setCurrentlyValidatingElement$1(null);
        }
      }

      function validateChildKeys(node, parentType) {
        {
          if (typeof node !== "object") {
            return;
          }
          if (isArray(node)) {
            for (var i = 0; i < node.length; i++) {
              var child = node[i];
              if (isValidElement(child)) {
                validateExplicitKey(child, parentType);
              }
            }
          } else if (isValidElement(node)) {
            if (node._store) {
              node._store.validated = true;
            }
          } else if (node) {
            var iteratorFn = getIteratorFn(node);
            if (typeof iteratorFn === "function") {
              if (iteratorFn !== node.entries) {
                var iterator = iteratorFn.call(node);
                var step;
                while (!(step = iterator.next()).done) {
                  if (isValidElement(step.value)) {
                    validateExplicitKey(step.value, parentType);
                  }
                }
              }
            }
          }
        }
      }

      function validatePropTypes(element) {
        {
          var type = element.type;
          if (type === null || type === void 0 || typeof type === "string") {
            return;
          }
          var propTypes;
          if (typeof type === "function") {
            propTypes = type.propTypes;
          } else if (typeof type === "object" && (type.$$typeof === REACT_FORWARD_REF_TYPE || type.$$typeof === REACT_MEMO_TYPE)) {
            propTypes = type.propTypes;
          } else {
            return;
          }
          if (propTypes) {
            var name = getComponentNameFromType(type);
            checkPropTypes(propTypes, element.props, "prop", name, element);
          } else if (type.PropTypes !== void 0 && !propTypesMisspellWarningShown) {
            propTypesMisspellWarningShown = true;
            var _name = getComponentNameFromType(type);
            error("Component %s declared `PropTypes` instead of `propTypes`. Did you misspell the property assignment?", _name || "Unknown");
          }
          if (typeof type.getDefaultProps === "function" && !type.getDefaultProps.isReactClassApproved) {
            error("getDefaultProps is only used on classic React.createClass definitions. Use a static property named `defaultProps` instead.");
          }
        }
      }

      function validateFragmentProps(fragment) {
        {
          var keys = Object.keys(fragment.props);
          for (var i = 0; i < keys.length; i++) {
            var key = keys[i];
            if (key !== "children" && key !== "key") {
              setCurrentlyValidatingElement$1(fragment);
              error("Invalid prop `%s` supplied to `React.Fragment`. React.Fragment can only have `key` and `children` props.", key);
              setCurrentlyValidatingElement$1(null);
              break;
            }
          }
          if (fragment.ref !== null) {
            setCurrentlyValidatingElement$1(fragment);
            error("Invalid attribute `ref` supplied to `React.Fragment`.");
            setCurrentlyValidatingElement$1(null);
          }
        }
      }

      function jsxWithValidation(type, props, key, isStaticChildren, source, self2) {
        {
          var validType = isValidElementType(type);
          if (!validType) {
            var info = "";
            if (type === void 0 || typeof type === "object" && type !== null && Object.keys(type).length === 0) {
              info += " You likely forgot to export your component from the file it's defined in, or you might have mixed up default and named imports.";
            }
            var sourceInfo = getSourceInfoErrorAddendum(source);
            if (sourceInfo) {
              info += sourceInfo;
            } else {
              info += getDeclarationErrorAddendum();
            }
            var typeString;
            if (type === null) {
              typeString = "null";
            } else if (isArray(type)) {
              typeString = "array";
            } else if (type !== void 0 && type.$$typeof === REACT_ELEMENT_TYPE) {
              typeString = "<" + (getComponentNameFromType(type.type) || "Unknown") + " />";
              info = " Did you accidentally export a JSX literal instead of a component?";
            } else {
              typeString = typeof type;
            }
            error("React.jsx: type is invalid -- expected a string (for built-in components) or a class/function (for composite components) but got: %s.%s", typeString, info);
          }
          var element = jsxDEV(type, props, key, source, self2);
          if (element == null) {
            return element;
          }
          if (validType) {
            var children = props.children;
            if (children !== void 0) {
              if (isStaticChildren) {
                if (isArray(children)) {
                  for (var i = 0; i < children.length; i++) {
                    validateChildKeys(children[i], type);
                  }
                  if (Object.freeze) {
                    Object.freeze(children);
                  }
                } else {
                  error("React.jsx: Static children should always be an array. You are likely explicitly calling React.jsxs or React.jsxDEV. Use the Babel transform instead.");
                }
              } else {
                validateChildKeys(children, type);
              }
            }
          }
          if (type === REACT_FRAGMENT_TYPE) {
            validateFragmentProps(element);
          } else {
            validatePropTypes(element);
          }
          return element;
        }
      }

      function jsxWithValidationStatic(type, props, key) {
        {
          return jsxWithValidation(type, props, key, true);
        }
      }

      function jsxWithValidationDynamic(type, props, key) {
        {
          return jsxWithValidation(type, props, key, false);
        }
      }

      var jsx2 = jsxWithValidationDynamic;
      var jsxs2 = jsxWithValidationStatic;
      reactJsxRuntime_development.Fragment = REACT_FRAGMENT_TYPE;
      reactJsxRuntime_development.jsx = jsx2;
      reactJsxRuntime_development.jsxs = jsxs2;
    })();
  }
  (function (module) {
    {
      module.exports = reactJsxRuntime_development;
    }
  })(jsxRuntime);
  const jsx = jsxRuntime.exports.jsx;
  const jsxs = jsxRuntime.exports.jsxs;
  const Fragment = jsxRuntime.exports.Fragment;
  const React$1 = window["React"];
  window["React"].Component;
  const ErrorBoundary = window["__foc__"].ErrorBoundary;

  function PluginWrapper({
                           component,
                           props
                         }) {
    return /* @__PURE__ */ jsx(ErrorBoundary, {
      disableReset: true,
      children: React$1.createElement(component, props)
    });
  }

  function wrapCustomComponent(customComponent) {
    return (props) => /* @__PURE__ */ jsx(PluginWrapper, {
      component: customComponent,
      props
    });
  }

  const foc = window["__foc__"];
  const foo = window["__foo__"];
  const fos$3 = window["__fos__"];
  const fou = window["__fou__"];
  window["__fou__"].getFetchFunction;
  window["__fou__"].getFetchOrigin;
  const mui = window["__mui__"];
  const React = window["React"];
  window["React"].useEffect;
  const useMemo = window["React"].useMemo;
  window["React"].useState;
  const ReactDOM = window["ReactDOM"];
  const recoil = window["recoil"];
  if (typeof window !== "undefined") {
    window.React = React;
    window.ReactDOM = ReactDOM;
    window.recoil = recoil;
    window.__fos__ = fos$3;
    window.__foc__ = foc;
    window.__fou__ = fou;
    window.__foo__ = foo;
    window.__mui__ = mui;
  }

  function usingRegistry() {
    if (!window.__fo_plugin_registry__) {
      window.__fo_plugin_registry__ = new PluginComponentRegistry();
    }
    return window.__fo_plugin_registry__;
  }

  function registerComponent(registration) {
    if (!registration.activator) {
      registration.activator = () => true;
    }
    usingRegistry().register(registration);
  }

  var PluginComponentType = /* @__PURE__ */ ((PluginComponentType2) => {
    PluginComponentType2[PluginComponentType2["Visualizer"] = 0] = "Visualizer";
    PluginComponentType2[PluginComponentType2["Plot"] = 1] = "Plot";
    PluginComponentType2[PluginComponentType2["Panel"] = 2] = "Panel";
    PluginComponentType2[PluginComponentType2["Component"] = 3] = "Component";
    return PluginComponentType2;
  })(PluginComponentType || {});
  const DEFAULT_ACTIVATOR = () => true;

  function assert(ok, msg, printWarningOnly = false) {
    const failed = ok === false || ok === null || ok === void 0;
    if (failed && printWarningOnly)
      console.warn(msg);
    else if (failed)
      throw new Error(msg);
  }

  function warn(ok, msg) {
    assert(ok, msg, true);
  }

  const REQUIRED = ["name", "type", "component"];

  class PluginComponentRegistry {
    constructor() {
      __publicField(this, "data", /* @__PURE__ */ new Map());
      __publicField(this, "pluginDefinitions", /* @__PURE__ */ new Map());
      __publicField(this, "scripts", /* @__PURE__ */ new Set());
    }

    registerScript(name) {
      this.scripts.add(name);
    }

    registerPluginDefinition(pluginDefinition) {
      this.pluginDefinitions.set(pluginDefinition.name, pluginDefinition);
    }

    getPluginDefinition(name) {
      return this.pluginDefinitions.get(name);
    }

    hasScript(name) {
      return this.scripts.has(name);
    }

    register(registration) {
      const {name} = registration;
      if (typeof registration.activator !== "function") {
        registration.activator = DEFAULT_ACTIVATOR;
      }
      for (let fieldName of REQUIRED) {
        assert(
          registration[fieldName],
          `${fieldName} is required to register a Plugin Component`
        );
      }
      warn(
        !this.data.has(name),
        `${name} is already a registered Plugin Component`
      );
      warn(
        registration.type === 1,
        `${name} is a Plot Plugin Component. This is deprecated. Please use "Panel" instead.`
      );
      const wrappedRegistration = {
        ...registration,
        component: wrapCustomComponent(registration.component)
      };
      this.data.set(name, wrappedRegistration);
    }

    unregister(name) {
      return this.data.delete(name);
    }

    getByType(type) {
      const results = [];
      for (const registration of this.data.values()) {
        if (registration.type === type) {
          results.push(registration);
        }
      }
      return results;
    }

    clear() {
      this.data.clear();
    }
  }

  function usePluginSettings(pluginName, defaults) {
    const dataset = recoil.useRecoilValue(fos$3.dataset);
    const appConfig = recoil.useRecoilValue(fos$3.config);
    const settings = useMemo(() => {
      const datasetPlugins = lodash.exports.get(dataset, "appConfig.plugins", {});
      const appConfigPlugins = lodash.exports.get(appConfig, "plugins", {});
      return lodash.exports.merge(
        {...defaults},
        lodash.exports.get(appConfigPlugins, pluginName, {}),
        lodash.exports.get(datasetPlugins, pluginName, {})
      );
    }, [dataset, appConfig, pluginName, defaults]);
    return settings;
  }

  const DefaultSettings = () => {
    return {
      server: "http://localhost:5152"
    };
  };
  var reactIs$2 = {exports: {}};
  var reactIs_development$1 = {};
  /** @license React v17.0.2
   * react-is.development.js
   *
   * Copyright (c) Facebook, Inc. and its affiliates.
   *
   * This source code is licensed under the MIT license found in the
   * LICENSE file in the root directory of this source tree.
   */
  {
    (function () {
      var REACT_ELEMENT_TYPE = 60103;
      var REACT_PORTAL_TYPE = 60106;
      var REACT_FRAGMENT_TYPE = 60107;
      var REACT_STRICT_MODE_TYPE = 60108;
      var REACT_PROFILER_TYPE = 60114;
      var REACT_PROVIDER_TYPE = 60109;
      var REACT_CONTEXT_TYPE = 60110;
      var REACT_FORWARD_REF_TYPE = 60112;
      var REACT_SUSPENSE_TYPE = 60113;
      var REACT_SUSPENSE_LIST_TYPE = 60120;
      var REACT_MEMO_TYPE = 60115;
      var REACT_LAZY_TYPE = 60116;
      var REACT_BLOCK_TYPE = 60121;
      var REACT_SERVER_BLOCK_TYPE = 60122;
      var REACT_FUNDAMENTAL_TYPE = 60117;
      var REACT_DEBUG_TRACING_MODE_TYPE = 60129;
      var REACT_LEGACY_HIDDEN_TYPE = 60131;
      if (typeof Symbol === "function" && Symbol.for) {
        var symbolFor = Symbol.for;
        REACT_ELEMENT_TYPE = symbolFor("react.element");
        REACT_PORTAL_TYPE = symbolFor("react.portal");
        REACT_FRAGMENT_TYPE = symbolFor("react.fragment");
        REACT_STRICT_MODE_TYPE = symbolFor("react.strict_mode");
        REACT_PROFILER_TYPE = symbolFor("react.profiler");
        REACT_PROVIDER_TYPE = symbolFor("react.provider");
        REACT_CONTEXT_TYPE = symbolFor("react.context");
        REACT_FORWARD_REF_TYPE = symbolFor("react.forward_ref");
        REACT_SUSPENSE_TYPE = symbolFor("react.suspense");
        REACT_SUSPENSE_LIST_TYPE = symbolFor("react.suspense_list");
        REACT_MEMO_TYPE = symbolFor("react.memo");
        REACT_LAZY_TYPE = symbolFor("react.lazy");
        REACT_BLOCK_TYPE = symbolFor("react.block");
        REACT_SERVER_BLOCK_TYPE = symbolFor("react.server.block");
        REACT_FUNDAMENTAL_TYPE = symbolFor("react.fundamental");
        symbolFor("react.scope");
        symbolFor("react.opaque.id");
        REACT_DEBUG_TRACING_MODE_TYPE = symbolFor("react.debug_trace_mode");
        symbolFor("react.offscreen");
        REACT_LEGACY_HIDDEN_TYPE = symbolFor("react.legacy_hidden");
      }
      var enableScopeAPI = false;

      function isValidElementType(type) {
        if (typeof type === "string" || typeof type === "function") {
          return true;
        }
        if (type === REACT_FRAGMENT_TYPE || type === REACT_PROFILER_TYPE || type === REACT_DEBUG_TRACING_MODE_TYPE || type === REACT_STRICT_MODE_TYPE || type === REACT_SUSPENSE_TYPE || type === REACT_SUSPENSE_LIST_TYPE || type === REACT_LEGACY_HIDDEN_TYPE || enableScopeAPI) {
          return true;
        }
        if (typeof type === "object" && type !== null) {
          if (type.$$typeof === REACT_LAZY_TYPE || type.$$typeof === REACT_MEMO_TYPE || type.$$typeof === REACT_PROVIDER_TYPE || type.$$typeof === REACT_CONTEXT_TYPE || type.$$typeof === REACT_FORWARD_REF_TYPE || type.$$typeof === REACT_FUNDAMENTAL_TYPE || type.$$typeof === REACT_BLOCK_TYPE || type[0] === REACT_SERVER_BLOCK_TYPE) {
            return true;
          }
        }
        return false;
      }

      function typeOf(object) {
        if (typeof object === "object" && object !== null) {
          var $$typeof = object.$$typeof;
          switch ($$typeof) {
            case REACT_ELEMENT_TYPE:
              var type = object.type;
              switch (type) {
                case REACT_FRAGMENT_TYPE:
                case REACT_PROFILER_TYPE:
                case REACT_STRICT_MODE_TYPE:
                case REACT_SUSPENSE_TYPE:
                case REACT_SUSPENSE_LIST_TYPE:
                  return type;
                default:
                  var $$typeofType = type && type.$$typeof;
                  switch ($$typeofType) {
                    case REACT_CONTEXT_TYPE:
                    case REACT_FORWARD_REF_TYPE:
                    case REACT_LAZY_TYPE:
                    case REACT_MEMO_TYPE:
                    case REACT_PROVIDER_TYPE:
                      return $$typeofType;
                    default:
                      return $$typeof;
                  }
              }
            case REACT_PORTAL_TYPE:
              return $$typeof;
          }
        }
        return void 0;
      }

      var ContextConsumer = REACT_CONTEXT_TYPE;
      var ContextProvider = REACT_PROVIDER_TYPE;
      var Element = REACT_ELEMENT_TYPE;
      var ForwardRef = REACT_FORWARD_REF_TYPE;
      var Fragment2 = REACT_FRAGMENT_TYPE;
      var Lazy = REACT_LAZY_TYPE;
      var Memo = REACT_MEMO_TYPE;
      var Portal = REACT_PORTAL_TYPE;
      var Profiler = REACT_PROFILER_TYPE;
      var StrictMode = REACT_STRICT_MODE_TYPE;
      var Suspense = REACT_SUSPENSE_TYPE;
      var hasWarnedAboutDeprecatedIsAsyncMode = false;
      var hasWarnedAboutDeprecatedIsConcurrentMode = false;

      function isAsyncMode(object) {
        {
          if (!hasWarnedAboutDeprecatedIsAsyncMode) {
            hasWarnedAboutDeprecatedIsAsyncMode = true;
            console["warn"]("The ReactIs.isAsyncMode() alias has been deprecated, and will be removed in React 18+.");
          }
        }
        return false;
      }

      function isConcurrentMode(object) {
        {
          if (!hasWarnedAboutDeprecatedIsConcurrentMode) {
            hasWarnedAboutDeprecatedIsConcurrentMode = true;
            console["warn"]("The ReactIs.isConcurrentMode() alias has been deprecated, and will be removed in React 18+.");
          }
        }
        return false;
      }

      function isContextConsumer(object) {
        return typeOf(object) === REACT_CONTEXT_TYPE;
      }

      function isContextProvider(object) {
        return typeOf(object) === REACT_PROVIDER_TYPE;
      }

      function isElement(object) {
        return typeof object === "object" && object !== null && object.$$typeof === REACT_ELEMENT_TYPE;
      }

      function isForwardRef(object) {
        return typeOf(object) === REACT_FORWARD_REF_TYPE;
      }

      function isFragment(object) {
        return typeOf(object) === REACT_FRAGMENT_TYPE;
      }

      function isLazy(object) {
        return typeOf(object) === REACT_LAZY_TYPE;
      }

      function isMemo(object) {
        return typeOf(object) === REACT_MEMO_TYPE;
      }

      function isPortal(object) {
        return typeOf(object) === REACT_PORTAL_TYPE;
      }

      function isProfiler(object) {
        return typeOf(object) === REACT_PROFILER_TYPE;
      }

      function isStrictMode(object) {
        return typeOf(object) === REACT_STRICT_MODE_TYPE;
      }

      function isSuspense(object) {
        return typeOf(object) === REACT_SUSPENSE_TYPE;
      }

      reactIs_development$1.ContextConsumer = ContextConsumer;
      reactIs_development$1.ContextProvider = ContextProvider;
      reactIs_development$1.Element = Element;
      reactIs_development$1.ForwardRef = ForwardRef;
      reactIs_development$1.Fragment = Fragment2;
      reactIs_development$1.Lazy = Lazy;
      reactIs_development$1.Memo = Memo;
      reactIs_development$1.Portal = Portal;
      reactIs_development$1.Profiler = Profiler;
      reactIs_development$1.StrictMode = StrictMode;
      reactIs_development$1.Suspense = Suspense;
      reactIs_development$1.isAsyncMode = isAsyncMode;
      reactIs_development$1.isConcurrentMode = isConcurrentMode;
      reactIs_development$1.isContextConsumer = isContextConsumer;
      reactIs_development$1.isContextProvider = isContextProvider;
      reactIs_development$1.isElement = isElement;
      reactIs_development$1.isForwardRef = isForwardRef;
      reactIs_development$1.isFragment = isFragment;
      reactIs_development$1.isLazy = isLazy;
      reactIs_development$1.isMemo = isMemo;
      reactIs_development$1.isPortal = isPortal;
      reactIs_development$1.isProfiler = isProfiler;
      reactIs_development$1.isStrictMode = isStrictMode;
      reactIs_development$1.isSuspense = isSuspense;
      reactIs_development$1.isValidElementType = isValidElementType;
      reactIs_development$1.typeOf = typeOf;
    })();
  }
  (function (module) {
    {
      module.exports = reactIs_development$1;
    }
  })(reactIs$2);

  function stylis_min(W2) {
    function M2(d, c2, e, h, a) {
      for (var m = 0, b2 = 0, v2 = 0, n = 0, q2, g2, x2 = 0, K2 = 0, k2, u2 = k2 = q2 = 0, l = 0, r2 = 0, I2 = 0, t = 0, B3 = e.length, J2 = B3 - 1, y2, f = "", p = "", F3 = "", G3 = "", C2; l < B3;) {
        g2 = e.charCodeAt(l);
        l === J2 && 0 !== b2 + n + v2 + m && (0 !== b2 && (g2 = 47 === b2 ? 10 : 47), n = v2 = m = 0, B3++, J2++);
        if (0 === b2 + n + v2 + m) {
          if (l === J2 && (0 < r2 && (f = f.replace(N2, "")), 0 < f.trim().length)) {
            switch (g2) {
              case 32:
              case 9:
              case 59:
              case 13:
              case 10:
                break;
              default:
                f += e.charAt(l);
            }
            g2 = 59;
          }
          switch (g2) {
            case 123:
              f = f.trim();
              q2 = f.charCodeAt(0);
              k2 = 1;
              for (t = ++l; l < B3;) {
                switch (g2 = e.charCodeAt(l)) {
                  case 123:
                    k2++;
                    break;
                  case 125:
                    k2--;
                    break;
                  case 47:
                    switch (g2 = e.charCodeAt(l + 1)) {
                      case 42:
                      case 47:
                        a: {
                          for (u2 = l + 1; u2 < J2; ++u2) {
                            switch (e.charCodeAt(u2)) {
                              case 47:
                                if (42 === g2 && 42 === e.charCodeAt(u2 - 1) && l + 2 !== u2) {
                                  l = u2 + 1;
                                  break a;
                                }
                                break;
                              case 10:
                                if (47 === g2) {
                                  l = u2 + 1;
                                  break a;
                                }
                            }
                          }
                          l = u2;
                        }
                    }
                    break;
                  case 91:
                    g2++;
                  case 40:
                    g2++;
                  case 34:
                  case 39:
                    for (; l++ < J2 && e.charCodeAt(l) !== g2;) {
                    }
                }
                if (0 === k2)
                  break;
                l++;
              }
              k2 = e.substring(t, l);
              0 === q2 && (q2 = (f = f.replace(ca, "").trim()).charCodeAt(0));
              switch (q2) {
                case 64:
                  0 < r2 && (f = f.replace(N2, ""));
                  g2 = f.charCodeAt(1);
                  switch (g2) {
                    case 100:
                    case 109:
                    case 115:
                    case 45:
                      r2 = c2;
                      break;
                    default:
                      r2 = O2;
                  }
                  k2 = M2(c2, r2, k2, g2, a + 1);
                  t = k2.length;
                  0 < A && (r2 = X2(O2, f, I2), C2 = H2(3, k2, r2, c2, D2, z2, t, g2, a, h), f = r2.join(""), void 0 !== C2 && 0 === (t = (k2 = C2.trim()).length) && (g2 = 0, k2 = ""));
                  if (0 < t)
                    switch (g2) {
                      case 115:
                        f = f.replace(da, ea);
                      case 100:
                      case 109:
                      case 45:
                        k2 = f + "{" + k2 + "}";
                        break;
                      case 107:
                        f = f.replace(fa, "$1 $2");
                        k2 = f + "{" + k2 + "}";
                        k2 = 1 === w2 || 2 === w2 && L2("@" + k2, 3) ? "@-webkit-" + k2 + "@" + k2 : "@" + k2;
                        break;
                      default:
                        k2 = f + k2, 112 === h && (k2 = (p += k2, ""));
                    }
                  else
                    k2 = "";
                  break;
                default:
                  k2 = M2(c2, X2(c2, f, I2), k2, h, a + 1);
              }
              F3 += k2;
              k2 = I2 = r2 = u2 = q2 = 0;
              f = "";
              g2 = e.charCodeAt(++l);
              break;
            case 125:
            case 59:
              f = (0 < r2 ? f.replace(N2, "") : f).trim();
              if (1 < (t = f.length))
                switch (0 === u2 && (q2 = f.charCodeAt(0), 45 === q2 || 96 < q2 && 123 > q2) && (t = (f = f.replace(" ", ":")).length), 0 < A && void 0 !== (C2 = H2(1, f, c2, d, D2, z2, p.length, h, a, h)) && 0 === (t = (f = C2.trim()).length) && (f = "\0\0"), q2 = f.charCodeAt(0), g2 = f.charCodeAt(1), q2) {
                  case 0:
                    break;
                  case 64:
                    if (105 === g2 || 99 === g2) {
                      G3 += f + e.charAt(l);
                      break;
                    }
                  default:
                    58 !== f.charCodeAt(t - 1) && (p += P(f, q2, g2, f.charCodeAt(2)));
                }
              I2 = r2 = u2 = q2 = 0;
              f = "";
              g2 = e.charCodeAt(++l);
          }
        }
        switch (g2) {
          case 13:
          case 10:
            47 === b2 ? b2 = 0 : 0 === 1 + q2 && 107 !== h && 0 < f.length && (r2 = 1, f += "\0");
            0 < A * Y2 && H2(0, f, c2, d, D2, z2, p.length, h, a, h);
            z2 = 1;
            D2++;
            break;
          case 59:
          case 125:
            if (0 === b2 + n + v2 + m) {
              z2++;
              break;
            }
          default:
            z2++;
            y2 = e.charAt(l);
            switch (g2) {
              case 9:
              case 32:
                if (0 === n + m + b2)
                  switch (x2) {
                    case 44:
                    case 58:
                    case 9:
                    case 32:
                      y2 = "";
                      break;
                    default:
                      32 !== g2 && (y2 = " ");
                  }
                break;
              case 0:
                y2 = "\\0";
                break;
              case 12:
                y2 = "\\f";
                break;
              case 11:
                y2 = "\\v";
                break;
              case 38:
                0 === n + b2 + m && (r2 = I2 = 1, y2 = "\f" + y2);
                break;
              case 108:
                if (0 === n + b2 + m + E2 && 0 < u2)
                  switch (l - u2) {
                    case 2:
                      112 === x2 && 58 === e.charCodeAt(l - 3) && (E2 = x2);
                    case 8:
                      111 === K2 && (E2 = K2);
                  }
                break;
              case 58:
                0 === n + b2 + m && (u2 = l);
                break;
              case 44:
                0 === b2 + v2 + n + m && (r2 = 1, y2 += "\r");
                break;
              case 34:
              case 39:
                0 === b2 && (n = n === g2 ? 0 : 0 === n ? g2 : n);
                break;
              case 91:
                0 === n + b2 + v2 && m++;
                break;
              case 93:
                0 === n + b2 + v2 && m--;
                break;
              case 41:
                0 === n + b2 + m && v2--;
                break;
              case 40:
                if (0 === n + b2 + m) {
                  if (0 === q2)
                    switch (2 * x2 + 3 * K2) {
                      case 533:
                        break;
                      default:
                        q2 = 1;
                    }
                  v2++;
                }
                break;
              case 64:
                0 === b2 + v2 + n + m + u2 + k2 && (k2 = 1);
                break;
              case 42:
              case 47:
                if (!(0 < n + m + v2))
                  switch (b2) {
                    case 0:
                      switch (2 * g2 + 3 * e.charCodeAt(l + 1)) {
                        case 235:
                          b2 = 47;
                          break;
                        case 220:
                          t = l, b2 = 42;
                      }
                      break;
                    case 42:
                      47 === g2 && 42 === x2 && t + 2 !== l && (33 === e.charCodeAt(t + 2) && (p += e.substring(t, l + 1)), y2 = "", b2 = 0);
                  }
            }
            0 === b2 && (f += y2);
        }
        K2 = x2;
        x2 = g2;
        l++;
      }
      t = p.length;
      if (0 < t) {
        r2 = c2;
        if (0 < A && (C2 = H2(2, p, r2, d, D2, z2, t, h, a, h), void 0 !== C2 && 0 === (p = C2).length))
          return G3 + p + F3;
        p = r2.join(",") + "{" + p + "}";
        if (0 !== w2 * E2) {
          2 !== w2 || L2(p, 2) || (E2 = 0);
          switch (E2) {
            case 111:
              p = p.replace(ha, ":-moz-$1") + p;
              break;
            case 112:
              p = p.replace(Q2, "::-webkit-input-$1") + p.replace(Q2, "::-moz-$1") + p.replace(Q2, ":-ms-input-$1") + p;
          }
          E2 = 0;
        }
      }
      return G3 + p + F3;
    }

    function X2(d, c2, e) {
      var h = c2.trim().split(ia);
      c2 = h;
      var a = h.length, m = d.length;
      switch (m) {
        case 0:
        case 1:
          var b2 = 0;
          for (d = 0 === m ? "" : d[0] + " "; b2 < a; ++b2) {
            c2[b2] = Z2(d, c2[b2], e).trim();
          }
          break;
        default:
          var v2 = b2 = 0;
          for (c2 = []; b2 < a; ++b2) {
            for (var n = 0; n < m; ++n) {
              c2[v2++] = Z2(d[n] + " ", h[b2], e).trim();
            }
          }
      }
      return c2;
    }

    function Z2(d, c2, e) {
      var h = c2.charCodeAt(0);
      33 > h && (h = (c2 = c2.trim()).charCodeAt(0));
      switch (h) {
        case 38:
          return c2.replace(F2, "$1" + d.trim());
        case 58:
          return d.trim() + c2.replace(F2, "$1" + d.trim());
        default:
          if (0 < 1 * e && 0 < c2.indexOf("\f"))
            return c2.replace(F2, (58 === d.charCodeAt(0) ? "" : "$1") + d.trim());
      }
      return d + c2;
    }

    function P(d, c2, e, h) {
      var a = d + ";", m = 2 * c2 + 3 * e + 4 * h;
      if (944 === m) {
        d = a.indexOf(":", 9) + 1;
        var b2 = a.substring(d, a.length - 1).trim();
        b2 = a.substring(0, d).trim() + b2 + ";";
        return 1 === w2 || 2 === w2 && L2(b2, 1) ? "-webkit-" + b2 + b2 : b2;
      }
      if (0 === w2 || 2 === w2 && !L2(a, 1))
        return a;
      switch (m) {
        case 1015:
          return 97 === a.charCodeAt(10) ? "-webkit-" + a + a : a;
        case 951:
          return 116 === a.charCodeAt(3) ? "-webkit-" + a + a : a;
        case 963:
          return 110 === a.charCodeAt(5) ? "-webkit-" + a + a : a;
        case 1009:
          if (100 !== a.charCodeAt(4))
            break;
        case 969:
        case 942:
          return "-webkit-" + a + a;
        case 978:
          return "-webkit-" + a + "-moz-" + a + a;
        case 1019:
        case 983:
          return "-webkit-" + a + "-moz-" + a + "-ms-" + a + a;
        case 883:
          if (45 === a.charCodeAt(8))
            return "-webkit-" + a + a;
          if (0 < a.indexOf("image-set(", 11))
            return a.replace(ja, "$1-webkit-$2") + a;
          break;
        case 932:
          if (45 === a.charCodeAt(4))
            switch (a.charCodeAt(5)) {
              case 103:
                return "-webkit-box-" + a.replace("-grow", "") + "-webkit-" + a + "-ms-" + a.replace("grow", "positive") + a;
              case 115:
                return "-webkit-" + a + "-ms-" + a.replace("shrink", "negative") + a;
              case 98:
                return "-webkit-" + a + "-ms-" + a.replace("basis", "preferred-size") + a;
            }
          return "-webkit-" + a + "-ms-" + a + a;
        case 964:
          return "-webkit-" + a + "-ms-flex-" + a + a;
        case 1023:
          if (99 !== a.charCodeAt(8))
            break;
          b2 = a.substring(a.indexOf(":", 15)).replace("flex-", "").replace("space-between", "justify");
          return "-webkit-box-pack" + b2 + "-webkit-" + a + "-ms-flex-pack" + b2 + a;
        case 1005:
          return ka.test(a) ? a.replace(aa, ":-webkit-") + a.replace(aa, ":-moz-") + a : a;
        case 1e3:
          b2 = a.substring(13).trim();
          c2 = b2.indexOf("-") + 1;
          switch (b2.charCodeAt(0) + b2.charCodeAt(c2)) {
            case 226:
              b2 = a.replace(G2, "tb");
              break;
            case 232:
              b2 = a.replace(G2, "tb-rl");
              break;
            case 220:
              b2 = a.replace(G2, "lr");
              break;
            default:
              return a;
          }
          return "-webkit-" + a + "-ms-" + b2 + a;
        case 1017:
          if (-1 === a.indexOf("sticky", 9))
            break;
        case 975:
          c2 = (a = d).length - 10;
          b2 = (33 === a.charCodeAt(c2) ? a.substring(0, c2) : a).substring(d.indexOf(":", 7) + 1).trim();
          switch (m = b2.charCodeAt(0) + (b2.charCodeAt(7) | 0)) {
            case 203:
              if (111 > b2.charCodeAt(8))
                break;
            case 115:
              a = a.replace(b2, "-webkit-" + b2) + ";" + a;
              break;
            case 207:
            case 102:
              a = a.replace(b2, "-webkit-" + (102 < m ? "inline-" : "") + "box") + ";" + a.replace(b2, "-webkit-" + b2) + ";" + a.replace(b2, "-ms-" + b2 + "box") + ";" + a;
          }
          return a + ";";
        case 938:
          if (45 === a.charCodeAt(5))
            switch (a.charCodeAt(6)) {
              case 105:
                return b2 = a.replace("-items", ""), "-webkit-" + a + "-webkit-box-" + b2 + "-ms-flex-" + b2 + a;
              case 115:
                return "-webkit-" + a + "-ms-flex-item-" + a.replace(ba, "") + a;
              default:
                return "-webkit-" + a + "-ms-flex-line-pack" + a.replace("align-content", "").replace(ba, "") + a;
            }
          break;
        case 973:
        case 989:
          if (45 !== a.charCodeAt(3) || 122 === a.charCodeAt(4))
            break;
        case 931:
        case 953:
          if (true === la.test(d))
            return 115 === (b2 = d.substring(d.indexOf(":") + 1)).charCodeAt(0) ? P(d.replace("stretch", "fill-available"), c2, e, h).replace(":fill-available", ":stretch") : a.replace(b2, "-webkit-" + b2) + a.replace(b2, "-moz-" + b2.replace("fill-", "")) + a;
          break;
        case 962:
          if (a = "-webkit-" + a + (102 === a.charCodeAt(5) ? "-ms-" + a : "") + a, 211 === e + h && 105 === a.charCodeAt(13) && 0 < a.indexOf("transform", 10))
            return a.substring(0, a.indexOf(";", 27) + 1).replace(ma, "$1-webkit-$2") + a;
      }
      return a;
    }

    function L2(d, c2) {
      var e = d.indexOf(1 === c2 ? ":" : "{"), h = d.substring(0, 3 !== c2 ? e : 10);
      e = d.substring(e + 1, d.length - 1);
      return R2(2 !== c2 ? h : h.replace(na, "$1"), e, c2);
    }

    function ea(d, c2) {
      var e = P(c2, c2.charCodeAt(0), c2.charCodeAt(1), c2.charCodeAt(2));
      return e !== c2 + ";" ? e.replace(oa, " or ($1)").substring(4) : "(" + c2 + ")";
    }

    function H2(d, c2, e, h, a, m, b2, v2, n, q2) {
      for (var g2 = 0, x2 = c2, w3; g2 < A; ++g2) {
        switch (w3 = S2[g2].call(B2, d, x2, e, h, a, m, b2, v2, n, q2)) {
          case void 0:
          case false:
          case true:
          case null:
            break;
          default:
            x2 = w3;
        }
      }
      if (x2 !== c2)
        return x2;
    }

    function T2(d) {
      switch (d) {
        case void 0:
        case null:
          A = S2.length = 0;
          break;
        default:
          if ("function" === typeof d)
            S2[A++] = d;
          else if ("object" === typeof d)
            for (var c2 = 0, e = d.length; c2 < e; ++c2) {
              T2(d[c2]);
            }
          else
            Y2 = !!d | 0;
      }
      return T2;
    }

    function U2(d) {
      d = d.prefix;
      void 0 !== d && (R2 = null, d ? "function" !== typeof d ? w2 = 1 : (w2 = 2, R2 = d) : w2 = 0);
      return U2;
    }

    function B2(d, c2) {
      var e = d;
      33 > e.charCodeAt(0) && (e = e.trim());
      V2 = e;
      e = [V2];
      if (0 < A) {
        var h = H2(-1, c2, e, e, D2, z2, 0, 0, 0, 0);
        void 0 !== h && "string" === typeof h && (c2 = h);
      }
      var a = M2(O2, e, c2, 0, 0);
      0 < A && (h = H2(-2, a, e, e, D2, z2, a.length, 0, 0, 0), void 0 !== h && (a = h));
      V2 = "";
      E2 = 0;
      z2 = D2 = 1;
      return a;
    }

    var ca = /^\0+/g, N2 = /[\0\r\f]/g, aa = /: */g, ka = /zoo|gra/, ma = /([,: ])(transform)/g, ia = /,\r+?/g,
      F2 = /([\t\r\n ])*\f?&/g, fa = /@(k\w+)\s*(\S*)\s*/, Q2 = /::(place)/g, ha = /:(read-only)/g,
      G2 = /[svh]\w+-[tblr]{2}/, da = /\(\s*(.*)\s*\)/g, oa = /([\s\S]*?);/g, ba = /-self|flex-/g,
      na = /[^]*?(:[rp][el]a[\w-]+)[^]*/, la = /stretch|:\s*\w+\-(?:conte|avail)/, ja = /([^-])(image-set\()/, z2 = 1,
      D2 = 1, E2 = 0, w2 = 1, O2 = [], S2 = [], A = 0, R2 = null, Y2 = 0, V2 = "";
    B2.use = T2;
    B2.set = U2;
    void 0 !== W2 && U2(W2);
    return B2;
  }

  var unitlessKeys = {
    animationIterationCount: 1,
    borderImageOutset: 1,
    borderImageSlice: 1,
    borderImageWidth: 1,
    boxFlex: 1,
    boxFlexGroup: 1,
    boxOrdinalGroup: 1,
    columnCount: 1,
    columns: 1,
    flex: 1,
    flexGrow: 1,
    flexPositive: 1,
    flexShrink: 1,
    flexNegative: 1,
    flexOrder: 1,
    gridRow: 1,
    gridRowEnd: 1,
    gridRowSpan: 1,
    gridRowStart: 1,
    gridColumn: 1,
    gridColumnEnd: 1,
    gridColumnSpan: 1,
    gridColumnStart: 1,
    msGridRow: 1,
    msGridRowSpan: 1,
    msGridColumn: 1,
    msGridColumnSpan: 1,
    fontWeight: 1,
    lineHeight: 1,
    opacity: 1,
    order: 1,
    orphans: 1,
    tabSize: 1,
    widows: 1,
    zIndex: 1,
    zoom: 1,
    WebkitLineClamp: 1,
    fillOpacity: 1,
    floodOpacity: 1,
    stopOpacity: 1,
    strokeDasharray: 1,
    strokeDashoffset: 1,
    strokeMiterlimit: 1,
    strokeOpacity: 1,
    strokeWidth: 1
  };

  function memoize(fn) {
    var cache = /* @__PURE__ */ Object.create(null);
    return function (arg) {
      if (cache[arg] === void 0)
        cache[arg] = fn(arg);
      return cache[arg];
    };
  }

  var reactPropsRegex = /^((children|dangerouslySetInnerHTML|key|ref|autoFocus|defaultValue|defaultChecked|innerHTML|suppressContentEditableWarning|suppressHydrationWarning|valueLink|abbr|accept|acceptCharset|accessKey|action|allow|allowUserMedia|allowPaymentRequest|allowFullScreen|allowTransparency|alt|async|autoComplete|autoPlay|capture|cellPadding|cellSpacing|challenge|charSet|checked|cite|classID|className|cols|colSpan|content|contentEditable|contextMenu|controls|controlsList|coords|crossOrigin|data|dateTime|decoding|default|defer|dir|disabled|disablePictureInPicture|download|draggable|encType|enterKeyHint|form|formAction|formEncType|formMethod|formNoValidate|formTarget|frameBorder|headers|height|hidden|high|href|hrefLang|htmlFor|httpEquiv|id|inputMode|integrity|is|keyParams|keyType|kind|label|lang|list|loading|loop|low|marginHeight|marginWidth|max|maxLength|media|mediaGroup|method|min|minLength|multiple|muted|name|nonce|noValidate|open|optimum|pattern|placeholder|playsInline|poster|preload|profile|radioGroup|readOnly|referrerPolicy|rel|required|reversed|role|rows|rowSpan|sandbox|scope|scoped|scrolling|seamless|selected|shape|size|sizes|slot|span|spellCheck|src|srcDoc|srcLang|srcSet|start|step|style|summary|tabIndex|target|title|translate|type|useMap|value|width|wmode|wrap|about|datatype|inlist|prefix|property|resource|typeof|vocab|autoCapitalize|autoCorrect|autoSave|color|incremental|fallback|inert|itemProp|itemScope|itemType|itemID|itemRef|on|option|results|security|unselectable|accentHeight|accumulate|additive|alignmentBaseline|allowReorder|alphabetic|amplitude|arabicForm|ascent|attributeName|attributeType|autoReverse|azimuth|baseFrequency|baselineShift|baseProfile|bbox|begin|bias|by|calcMode|capHeight|clip|clipPathUnits|clipPath|clipRule|colorInterpolation|colorInterpolationFilters|colorProfile|colorRendering|contentScriptType|contentStyleType|cursor|cx|cy|d|decelerate|descent|diffuseConstant|direction|display|divisor|dominantBaseline|dur|dx|dy|edgeMode|elevation|enableBackground|end|exponent|externalResourcesRequired|fill|fillOpacity|fillRule|filter|filterRes|filterUnits|floodColor|floodOpacity|focusable|fontFamily|fontSize|fontSizeAdjust|fontStretch|fontStyle|fontVariant|fontWeight|format|from|fr|fx|fy|g1|g2|glyphName|glyphOrientationHorizontal|glyphOrientationVertical|glyphRef|gradientTransform|gradientUnits|hanging|horizAdvX|horizOriginX|ideographic|imageRendering|in|in2|intercept|k|k1|k2|k3|k4|kernelMatrix|kernelUnitLength|kerning|keyPoints|keySplines|keyTimes|lengthAdjust|letterSpacing|lightingColor|limitingConeAngle|local|markerEnd|markerMid|markerStart|markerHeight|markerUnits|markerWidth|mask|maskContentUnits|maskUnits|mathematical|mode|numOctaves|offset|opacity|operator|order|orient|orientation|origin|overflow|overlinePosition|overlineThickness|panose1|paintOrder|pathLength|patternContentUnits|patternTransform|patternUnits|pointerEvents|points|pointsAtX|pointsAtY|pointsAtZ|preserveAlpha|preserveAspectRatio|primitiveUnits|r|radius|refX|refY|renderingIntent|repeatCount|repeatDur|requiredExtensions|requiredFeatures|restart|result|rotate|rx|ry|scale|seed|shapeRendering|slope|spacing|specularConstant|specularExponent|speed|spreadMethod|startOffset|stdDeviation|stemh|stemv|stitchTiles|stopColor|stopOpacity|strikethroughPosition|strikethroughThickness|string|stroke|strokeDasharray|strokeDashoffset|strokeLinecap|strokeLinejoin|strokeMiterlimit|strokeOpacity|strokeWidth|surfaceScale|systemLanguage|tableValues|targetX|targetY|textAnchor|textDecoration|textRendering|textLength|to|transform|u1|u2|underlinePosition|underlineThickness|unicode|unicodeBidi|unicodeRange|unitsPerEm|vAlphabetic|vHanging|vIdeographic|vMathematical|values|vectorEffect|version|vertAdvY|vertOriginX|vertOriginY|viewBox|viewTarget|visibility|widths|wordSpacing|writingMode|x|xHeight|x1|x2|xChannelSelector|xlinkActuate|xlinkArcrole|xlinkHref|xlinkRole|xlinkShow|xlinkTitle|xlinkType|xmlBase|xmlns|xmlnsXlink|xmlLang|xmlSpace|y|y1|y2|yChannelSelector|z|zoomAndPan|for|class|autofocus)|(([Dd][Aa][Tt][Aa]|[Aa][Rr][Ii][Aa]|x)-.*))$/;
  var isPropValid = /* @__PURE__ */ memoize(
    function (prop) {
      return reactPropsRegex.test(prop) || prop.charCodeAt(0) === 111 && prop.charCodeAt(1) === 110 && prop.charCodeAt(2) < 91;
    }
  );
  var reactIs$1 = {exports: {}};
  var reactIs_development = {};
  /** @license React v16.13.1
   * react-is.development.js
   *
   * Copyright (c) Facebook, Inc. and its affiliates.
   *
   * This source code is licensed under the MIT license found in the
   * LICENSE file in the root directory of this source tree.
   */
  {
    (function () {
      var hasSymbol = typeof Symbol === "function" && Symbol.for;
      var REACT_ELEMENT_TYPE = hasSymbol ? Symbol.for("react.element") : 60103;
      var REACT_PORTAL_TYPE = hasSymbol ? Symbol.for("react.portal") : 60106;
      var REACT_FRAGMENT_TYPE = hasSymbol ? Symbol.for("react.fragment") : 60107;
      var REACT_STRICT_MODE_TYPE = hasSymbol ? Symbol.for("react.strict_mode") : 60108;
      var REACT_PROFILER_TYPE = hasSymbol ? Symbol.for("react.profiler") : 60114;
      var REACT_PROVIDER_TYPE = hasSymbol ? Symbol.for("react.provider") : 60109;
      var REACT_CONTEXT_TYPE = hasSymbol ? Symbol.for("react.context") : 60110;
      var REACT_ASYNC_MODE_TYPE = hasSymbol ? Symbol.for("react.async_mode") : 60111;
      var REACT_CONCURRENT_MODE_TYPE = hasSymbol ? Symbol.for("react.concurrent_mode") : 60111;
      var REACT_FORWARD_REF_TYPE = hasSymbol ? Symbol.for("react.forward_ref") : 60112;
      var REACT_SUSPENSE_TYPE = hasSymbol ? Symbol.for("react.suspense") : 60113;
      var REACT_SUSPENSE_LIST_TYPE = hasSymbol ? Symbol.for("react.suspense_list") : 60120;
      var REACT_MEMO_TYPE = hasSymbol ? Symbol.for("react.memo") : 60115;
      var REACT_LAZY_TYPE = hasSymbol ? Symbol.for("react.lazy") : 60116;
      var REACT_BLOCK_TYPE = hasSymbol ? Symbol.for("react.block") : 60121;
      var REACT_FUNDAMENTAL_TYPE = hasSymbol ? Symbol.for("react.fundamental") : 60117;
      var REACT_RESPONDER_TYPE = hasSymbol ? Symbol.for("react.responder") : 60118;
      var REACT_SCOPE_TYPE = hasSymbol ? Symbol.for("react.scope") : 60119;

      function isValidElementType(type) {
        return typeof type === "string" || typeof type === "function" || type === REACT_FRAGMENT_TYPE || type === REACT_CONCURRENT_MODE_TYPE || type === REACT_PROFILER_TYPE || type === REACT_STRICT_MODE_TYPE || type === REACT_SUSPENSE_TYPE || type === REACT_SUSPENSE_LIST_TYPE || typeof type === "object" && type !== null && (type.$$typeof === REACT_LAZY_TYPE || type.$$typeof === REACT_MEMO_TYPE || type.$$typeof === REACT_PROVIDER_TYPE || type.$$typeof === REACT_CONTEXT_TYPE || type.$$typeof === REACT_FORWARD_REF_TYPE || type.$$typeof === REACT_FUNDAMENTAL_TYPE || type.$$typeof === REACT_RESPONDER_TYPE || type.$$typeof === REACT_SCOPE_TYPE || type.$$typeof === REACT_BLOCK_TYPE);
      }

      function typeOf(object) {
        if (typeof object === "object" && object !== null) {
          var $$typeof = object.$$typeof;
          switch ($$typeof) {
            case REACT_ELEMENT_TYPE:
              var type = object.type;
              switch (type) {
                case REACT_ASYNC_MODE_TYPE:
                case REACT_CONCURRENT_MODE_TYPE:
                case REACT_FRAGMENT_TYPE:
                case REACT_PROFILER_TYPE:
                case REACT_STRICT_MODE_TYPE:
                case REACT_SUSPENSE_TYPE:
                  return type;
                default:
                  var $$typeofType = type && type.$$typeof;
                  switch ($$typeofType) {
                    case REACT_CONTEXT_TYPE:
                    case REACT_FORWARD_REF_TYPE:
                    case REACT_LAZY_TYPE:
                    case REACT_MEMO_TYPE:
                    case REACT_PROVIDER_TYPE:
                      return $$typeofType;
                    default:
                      return $$typeof;
                  }
              }
            case REACT_PORTAL_TYPE:
              return $$typeof;
          }
        }
        return void 0;
      }

      var AsyncMode = REACT_ASYNC_MODE_TYPE;
      var ConcurrentMode = REACT_CONCURRENT_MODE_TYPE;
      var ContextConsumer = REACT_CONTEXT_TYPE;
      var ContextProvider = REACT_PROVIDER_TYPE;
      var Element = REACT_ELEMENT_TYPE;
      var ForwardRef = REACT_FORWARD_REF_TYPE;
      var Fragment2 = REACT_FRAGMENT_TYPE;
      var Lazy = REACT_LAZY_TYPE;
      var Memo = REACT_MEMO_TYPE;
      var Portal = REACT_PORTAL_TYPE;
      var Profiler = REACT_PROFILER_TYPE;
      var StrictMode = REACT_STRICT_MODE_TYPE;
      var Suspense = REACT_SUSPENSE_TYPE;
      var hasWarnedAboutDeprecatedIsAsyncMode = false;

      function isAsyncMode(object) {
        {
          if (!hasWarnedAboutDeprecatedIsAsyncMode) {
            hasWarnedAboutDeprecatedIsAsyncMode = true;
            console["warn"]("The ReactIs.isAsyncMode() alias has been deprecated, and will be removed in React 17+. Update your code to use ReactIs.isConcurrentMode() instead. It has the exact same API.");
          }
        }
        return isConcurrentMode(object) || typeOf(object) === REACT_ASYNC_MODE_TYPE;
      }

      function isConcurrentMode(object) {
        return typeOf(object) === REACT_CONCURRENT_MODE_TYPE;
      }

      function isContextConsumer(object) {
        return typeOf(object) === REACT_CONTEXT_TYPE;
      }

      function isContextProvider(object) {
        return typeOf(object) === REACT_PROVIDER_TYPE;
      }

      function isElement(object) {
        return typeof object === "object" && object !== null && object.$$typeof === REACT_ELEMENT_TYPE;
      }

      function isForwardRef(object) {
        return typeOf(object) === REACT_FORWARD_REF_TYPE;
      }

      function isFragment(object) {
        return typeOf(object) === REACT_FRAGMENT_TYPE;
      }

      function isLazy(object) {
        return typeOf(object) === REACT_LAZY_TYPE;
      }

      function isMemo(object) {
        return typeOf(object) === REACT_MEMO_TYPE;
      }

      function isPortal(object) {
        return typeOf(object) === REACT_PORTAL_TYPE;
      }

      function isProfiler(object) {
        return typeOf(object) === REACT_PROFILER_TYPE;
      }

      function isStrictMode(object) {
        return typeOf(object) === REACT_STRICT_MODE_TYPE;
      }

      function isSuspense(object) {
        return typeOf(object) === REACT_SUSPENSE_TYPE;
      }

      reactIs_development.AsyncMode = AsyncMode;
      reactIs_development.ConcurrentMode = ConcurrentMode;
      reactIs_development.ContextConsumer = ContextConsumer;
      reactIs_development.ContextProvider = ContextProvider;
      reactIs_development.Element = Element;
      reactIs_development.ForwardRef = ForwardRef;
      reactIs_development.Fragment = Fragment2;
      reactIs_development.Lazy = Lazy;
      reactIs_development.Memo = Memo;
      reactIs_development.Portal = Portal;
      reactIs_development.Profiler = Profiler;
      reactIs_development.StrictMode = StrictMode;
      reactIs_development.Suspense = Suspense;
      reactIs_development.isAsyncMode = isAsyncMode;
      reactIs_development.isConcurrentMode = isConcurrentMode;
      reactIs_development.isContextConsumer = isContextConsumer;
      reactIs_development.isContextProvider = isContextProvider;
      reactIs_development.isElement = isElement;
      reactIs_development.isForwardRef = isForwardRef;
      reactIs_development.isFragment = isFragment;
      reactIs_development.isLazy = isLazy;
      reactIs_development.isMemo = isMemo;
      reactIs_development.isPortal = isPortal;
      reactIs_development.isProfiler = isProfiler;
      reactIs_development.isStrictMode = isStrictMode;
      reactIs_development.isSuspense = isSuspense;
      reactIs_development.isValidElementType = isValidElementType;
      reactIs_development.typeOf = typeOf;
    })();
  }
  (function (module) {
    {
      module.exports = reactIs_development;
    }
  })(reactIs$1);
  var reactIs = reactIs$1.exports;
  var REACT_STATICS = {
    childContextTypes: true,
    contextType: true,
    contextTypes: true,
    defaultProps: true,
    displayName: true,
    getDefaultProps: true,
    getDerivedStateFromError: true,
    getDerivedStateFromProps: true,
    mixins: true,
    propTypes: true,
    type: true
  };
  var KNOWN_STATICS = {
    name: true,
    length: true,
    prototype: true,
    caller: true,
    callee: true,
    arguments: true,
    arity: true
  };
  var FORWARD_REF_STATICS = {
    "$$typeof": true,
    render: true,
    defaultProps: true,
    displayName: true,
    propTypes: true
  };
  var MEMO_STATICS = {
    "$$typeof": true,
    compare: true,
    defaultProps: true,
    displayName: true,
    propTypes: true,
    type: true
  };
  var TYPE_STATICS = {};
  TYPE_STATICS[reactIs.ForwardRef] = FORWARD_REF_STATICS;
  TYPE_STATICS[reactIs.Memo] = MEMO_STATICS;

  function getStatics(component) {
    if (reactIs.isMemo(component)) {
      return MEMO_STATICS;
    }
    return TYPE_STATICS[component["$$typeof"]] || REACT_STATICS;
  }

  var defineProperty = Object.defineProperty;
  var getOwnPropertyNames = Object.getOwnPropertyNames;
  var getOwnPropertySymbols = Object.getOwnPropertySymbols;
  var getOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;
  var getPrototypeOf = Object.getPrototypeOf;
  var objectPrototype = Object.prototype;

  function hoistNonReactStatics(targetComponent, sourceComponent, blacklist) {
    if (typeof sourceComponent !== "string") {
      if (objectPrototype) {
        var inheritedComponent = getPrototypeOf(sourceComponent);
        if (inheritedComponent && inheritedComponent !== objectPrototype) {
          hoistNonReactStatics(targetComponent, inheritedComponent, blacklist);
        }
      }
      var keys = getOwnPropertyNames(sourceComponent);
      if (getOwnPropertySymbols) {
        keys = keys.concat(getOwnPropertySymbols(sourceComponent));
      }
      var targetStatics = getStatics(targetComponent);
      var sourceStatics = getStatics(sourceComponent);
      for (var i = 0; i < keys.length; ++i) {
        var key = keys[i];
        if (!KNOWN_STATICS[key] && !(blacklist && blacklist[key]) && !(sourceStatics && sourceStatics[key]) && !(targetStatics && targetStatics[key])) {
          var descriptor = getOwnPropertyDescriptor(sourceComponent, key);
          try {
            defineProperty(targetComponent, key, descriptor);
          } catch (e) {
          }
        }
      }
    }
    return targetComponent;
  }

  var hoistNonReactStatics_cjs = hoistNonReactStatics;
  const r = window["React"];
  window["React"].useState;
  const s = window["React"].useContext;
  window["React"].useMemo;
  window["React"].useEffect;
  const c = window["React"].useRef;
  const u = window["React"].createElement;
  window["React"].useLayoutEffect;

  function y() {
    return (y = Object.assign || function (e) {
      for (var t = 1; t < arguments.length; t++) {
        var n = arguments[t];
        for (var r2 in n)
          Object.prototype.hasOwnProperty.call(n, r2) && (e[r2] = n[r2]);
      }
      return e;
    }).apply(this, arguments);
  }

  var v = function (e, t) {
    for (var n = [e[0]], r2 = 0, o = t.length; r2 < o; r2 += 1)
      n.push(t[r2], e[r2 + 1]);
    return n;
  }, g = function (t) {
    return null !== t && "object" == typeof t && "[object Object]" === (t.toString ? t.toString() : Object.prototype.toString.call(t)) && !reactIs$2.exports.typeOf(t);
  }, S = Object.freeze([]), w = Object.freeze({});

  function E(e) {
    return "function" == typeof e;
  }

  function b(e) {
    return "string" == typeof e && e || e.displayName || e.name || "Component";
  }

  function _(e) {
    return e && "string" == typeof e.styledComponentId;
  }

  var N = "undefined" != typeof process && void 0 !== process.env && (process.env.REACT_APP_SC_ATTR || process.env.SC_ATTR) || "data-styled",
    C = "undefined" != typeof window && "HTMLElement" in window,
    I = Boolean("boolean" == typeof SC_DISABLE_SPEEDY ? SC_DISABLE_SPEEDY : "undefined" != typeof process && void 0 !== process.env && (void 0 !== process.env.REACT_APP_SC_DISABLE_SPEEDY && "" !== process.env.REACT_APP_SC_DISABLE_SPEEDY ? "false" !== process.env.REACT_APP_SC_DISABLE_SPEEDY && process.env.REACT_APP_SC_DISABLE_SPEEDY : void 0 !== process.env.SC_DISABLE_SPEEDY && "" !== process.env.SC_DISABLE_SPEEDY ? "false" !== process.env.SC_DISABLE_SPEEDY && process.env.SC_DISABLE_SPEEDY : true)),
    O = {
      1: "Cannot create styled-component for component: %s.\n\n",
      2: "Can't collect styles once you've consumed a `ServerStyleSheet`'s styles! `ServerStyleSheet` is a one off instance for each server-side render cycle.\n\n- Are you trying to reuse it across renders?\n- Are you accidentally calling collectStyles twice?\n\n",
      3: "Streaming SSR is only supported in a Node.js environment; Please do not try to call this method in the browser.\n\n",
      4: "The `StyleSheetManager` expects a valid target or sheet prop!\n\n- Does this error occur on the client and is your target falsy?\n- Does this error occur on the server and is the sheet falsy?\n\n",
      5: "The clone method cannot be used on the client!\n\n- Are you running in a client-like environment on the server?\n- Are you trying to run SSR on the client?\n\n",
      6: "Trying to insert a new style tag, but the given Node is unmounted!\n\n- Are you using a custom target that isn't mounted?\n- Does your document not have a valid head element?\n- Have you accidentally removed a style tag manually?\n\n",
      7: 'ThemeProvider: Please return an object from your "theme" prop function, e.g.\n\n```js\ntheme={() => ({})}\n```\n\n',
      8: 'ThemeProvider: Please make your "theme" prop an object.\n\n',
      9: "Missing document `<head>`\n\n",
      10: "Cannot find a StyleSheet instance. Usually this happens if there are multiple copies of styled-components loaded at once. Check out this issue for how to troubleshoot and fix the common cases where this situation can happen: https://github.com/styled-components/styled-components/issues/1941#issuecomment-417862021\n\n",
      11: "_This error was replaced with a dev-time warning, it will be deleted for v4 final._ [createGlobalStyle] received children which will not be rendered. Please use the component without passing children elements.\n\n",
      12: "It seems you are interpolating a keyframe declaration (%s) into an untagged string. This was supported in styled-components v3, but is not longer supported in v4 as keyframes are now injected on-demand. Please wrap your string in the css\\`\\` helper which ensures the styles are injected correctly. See https://www.styled-components.com/docs/api#css\n\n",
      13: "%s is not a styled component and cannot be referred to via component selector. See https://www.styled-components.com/docs/advanced#referring-to-other-components for more details.\n\n",
      14: 'ThemeProvider: "theme" prop is required.\n\n',
      15: "A stylis plugin has been supplied that is not named. We need a name for each plugin to be able to prevent styling collisions between different stylis configurations within the same app. Before you pass your plugin to `<StyleSheetManager stylisPlugins={[]}>`, please make sure each plugin is uniquely-named, e.g.\n\n```js\nObject.defineProperty(importedPlugin, 'name', { value: 'some-unique-name' });\n```\n\n",
      16: "Reached the limit of how many styled components may be created at group %s.\nYou may only create up to 1,073,741,824 components. If you're creating components dynamically,\nas for instance in your render method then you may be running into this limitation.\n\n",
      17: "CSSStyleSheet could not be found on HTMLStyleElement.\nHas styled-components' style tag been unmounted or altered by another script?\n"
    };

  function R() {
    for (var e = arguments.length <= 0 ? void 0 : arguments[0], t = [], n = 1, r2 = arguments.length; n < r2; n += 1)
      t.push(n < 0 || arguments.length <= n ? void 0 : arguments[n]);
    return t.forEach(function (t2) {
      e = e.replace(/%[a-z]/, t2);
    }), e;
  }

  function D(e) {
    for (var t = arguments.length, n = new Array(t > 1 ? t - 1 : 0), r2 = 1; r2 < t; r2++)
      n[r2 - 1] = arguments[r2];
    throw new Error(R.apply(void 0, [O[e]].concat(n)).trim());
  }

  var j = function () {
      function e(e2) {
        this.groupSizes = new Uint32Array(512), this.length = 512, this.tag = e2;
      }

      var t = e.prototype;
      return t.indexOfGroup = function (e2) {
        for (var t2 = 0, n = 0; n < e2; n++)
          t2 += this.groupSizes[n];
        return t2;
      }, t.insertRules = function (e2, t2) {
        if (e2 >= this.groupSizes.length) {
          for (var n = this.groupSizes, r2 = n.length, o = r2; e2 >= o;)
            (o <<= 1) < 0 && D(16, "" + e2);
          this.groupSizes = new Uint32Array(o), this.groupSizes.set(n), this.length = o;
          for (var s2 = r2; s2 < o; s2++)
            this.groupSizes[s2] = 0;
        }
        for (var i = this.indexOfGroup(e2 + 1), a = 0, c2 = t2.length; a < c2; a++)
          this.tag.insertRule(i, t2[a]) && (this.groupSizes[e2]++, i++);
      }, t.clearGroup = function (e2) {
        if (e2 < this.length) {
          var t2 = this.groupSizes[e2], n = this.indexOfGroup(e2), r2 = n + t2;
          this.groupSizes[e2] = 0;
          for (var o = n; o < r2; o++)
            this.tag.deleteRule(n);
        }
      }, t.getGroup = function (e2) {
        var t2 = "";
        if (e2 >= this.length || 0 === this.groupSizes[e2])
          return t2;
        for (var n = this.groupSizes[e2], r2 = this.indexOfGroup(e2), o = r2 + n, s2 = r2; s2 < o; s2++)
          t2 += this.tag.getRule(s2) + "/*!sc*/\n";
        return t2;
      }, e;
    }(), T = /* @__PURE__ */ new Map(), x = /* @__PURE__ */ new Map(), k = 1, V = function (e) {
      if (T.has(e))
        return T.get(e);
      for (; x.has(k);)
        k++;
      var t = k++;
      return ((0 | t) < 0 || t > 1 << 30) && D(16, "" + t), T.set(e, t), x.set(t, e), t;
    }, B = function (e) {
      return x.get(e);
    }, z = function (e, t) {
      t >= k && (k = t + 1), T.set(e, t), x.set(t, e);
    }, M = "style[" + N + '][data-styled-version="5.3.11"]',
    G = new RegExp("^" + N + '\\.g(\\d+)\\[id="([\\w\\d-]+)"\\].*?"([^"]*)'), L = function (e, t, n) {
      for (var r2, o = n.split(","), s2 = 0, i = o.length; s2 < i; s2++)
        (r2 = o[s2]) && e.registerName(t, r2);
    }, F = function (e, t) {
      for (var n = (t.textContent || "").split("/*!sc*/\n"), r2 = [], o = 0, s2 = n.length; o < s2; o++) {
        var i = n[o].trim();
        if (i) {
          var a = i.match(G);
          if (a) {
            var c2 = 0 | parseInt(a[1], 10), u2 = a[2];
            0 !== c2 && (z(u2, c2), L(e, u2, a[3]), e.getTag().insertRules(c2, r2)), r2.length = 0;
          } else
            r2.push(i);
        }
      }
    }, Y = function () {
      return "undefined" != typeof __webpack_nonce__ ? __webpack_nonce__ : null;
    }, q = function (e) {
      var t = document.head, n = e || t, r2 = document.createElement("style"), o = function (e2) {
        for (var t2 = e2.childNodes, n2 = t2.length; n2 >= 0; n2--) {
          var r3 = t2[n2];
          if (r3 && 1 === r3.nodeType && r3.hasAttribute(N))
            return r3;
        }
      }(n), s2 = void 0 !== o ? o.nextSibling : null;
      r2.setAttribute(N, "active"), r2.setAttribute("data-styled-version", "5.3.11");
      var i = Y();
      return i && r2.setAttribute("nonce", i), n.insertBefore(r2, s2), r2;
    }, H = function () {
      function e(e2) {
        var t2 = this.element = q(e2);
        t2.appendChild(document.createTextNode("")), this.sheet = function (e3) {
          if (e3.sheet)
            return e3.sheet;
          for (var t3 = document.styleSheets, n = 0, r2 = t3.length; n < r2; n++) {
            var o = t3[n];
            if (o.ownerNode === e3)
              return o;
          }
          D(17);
        }(t2), this.length = 0;
      }

      var t = e.prototype;
      return t.insertRule = function (e2, t2) {
        try {
          return this.sheet.insertRule(t2, e2), this.length++, true;
        } catch (e3) {
          return false;
        }
      }, t.deleteRule = function (e2) {
        this.sheet.deleteRule(e2), this.length--;
      }, t.getRule = function (e2) {
        var t2 = this.sheet.cssRules[e2];
        return void 0 !== t2 && "string" == typeof t2.cssText ? t2.cssText : "";
      }, e;
    }(), $ = function () {
      function e(e2) {
        var t2 = this.element = q(e2);
        this.nodes = t2.childNodes, this.length = 0;
      }

      var t = e.prototype;
      return t.insertRule = function (e2, t2) {
        if (e2 <= this.length && e2 >= 0) {
          var n = document.createTextNode(t2), r2 = this.nodes[e2];
          return this.element.insertBefore(n, r2 || null), this.length++, true;
        }
        return false;
      }, t.deleteRule = function (e2) {
        this.element.removeChild(this.nodes[e2]), this.length--;
      }, t.getRule = function (e2) {
        return e2 < this.length ? this.nodes[e2].textContent : "";
      }, e;
    }(), W = function () {
      function e(e2) {
        this.rules = [], this.length = 0;
      }

      var t = e.prototype;
      return t.insertRule = function (e2, t2) {
        return e2 <= this.length && (this.rules.splice(e2, 0, t2), this.length++, true);
      }, t.deleteRule = function (e2) {
        this.rules.splice(e2, 1), this.length--;
      }, t.getRule = function (e2) {
        return e2 < this.length ? this.rules[e2] : "";
      }, e;
    }(), U = C, J = {isServer: !C, useCSSOMInjection: !I}, X = function () {
      function e(e2, t2, n) {
        void 0 === e2 && (e2 = w), void 0 === t2 && (t2 = {}), this.options = y({}, J, {}, e2), this.gs = t2, this.names = new Map(n), this.server = !!e2.isServer, !this.server && C && U && (U = false, function (e3) {
          for (var t3 = document.querySelectorAll(M), n2 = 0, r2 = t3.length; n2 < r2; n2++) {
            var o = t3[n2];
            o && "active" !== o.getAttribute(N) && (F(e3, o), o.parentNode && o.parentNode.removeChild(o));
          }
        }(this));
      }

      e.registerId = function (e2) {
        return V(e2);
      };
      var t = e.prototype;
      return t.reconstructWithOptions = function (t2, n) {
        return void 0 === n && (n = true), new e(y({}, this.options, {}, t2), this.gs, n && this.names || void 0);
      }, t.allocateGSInstance = function (e2) {
        return this.gs[e2] = (this.gs[e2] || 0) + 1;
      }, t.getTag = function () {
        return this.tag || (this.tag = (n = (t2 = this.options).isServer, r2 = t2.useCSSOMInjection, o = t2.target, e2 = n ? new W(o) : r2 ? new H(o) : new $(o), new j(e2)));
        var e2, t2, n, r2, o;
      }, t.hasNameForId = function (e2, t2) {
        return this.names.has(e2) && this.names.get(e2).has(t2);
      }, t.registerName = function (e2, t2) {
        if (V(e2), this.names.has(e2))
          this.names.get(e2).add(t2);
        else {
          var n = /* @__PURE__ */ new Set();
          n.add(t2), this.names.set(e2, n);
        }
      }, t.insertRules = function (e2, t2, n) {
        this.registerName(e2, t2), this.getTag().insertRules(V(e2), n);
      }, t.clearNames = function (e2) {
        this.names.has(e2) && this.names.get(e2).clear();
      }, t.clearRules = function (e2) {
        this.getTag().clearGroup(V(e2)), this.clearNames(e2);
      }, t.clearTag = function () {
        this.tag = void 0;
      }, t.toString = function () {
        return function (e2) {
          for (var t2 = e2.getTag(), n = t2.length, r2 = "", o = 0; o < n; o++) {
            var s2 = B(o);
            if (void 0 !== s2) {
              var i = e2.names.get(s2), a = t2.getGroup(o);
              if (i && a && i.size) {
                var c2 = N + ".g" + o + '[id="' + s2 + '"]', u2 = "";
                void 0 !== i && i.forEach(function (e3) {
                  e3.length > 0 && (u2 += e3 + ",");
                }), r2 += "" + a + c2 + '{content:"' + u2 + '"}/*!sc*/\n';
              }
            }
          }
          return r2;
        }(this);
      }, e;
    }(), Z = /(a)(d)/gi, K = function (e) {
      return String.fromCharCode(e + (e > 25 ? 39 : 97));
    };

  function Q(e) {
    var t, n = "";
    for (t = Math.abs(e); t > 52; t = t / 52 | 0)
      n = K(t % 52) + n;
    return (K(t % 52) + n).replace(Z, "$1-$2");
  }

  var ee = function (e, t) {
    for (var n = t.length; n;)
      e = 33 * e ^ t.charCodeAt(--n);
    return e;
  }, te = function (e) {
    return ee(5381, e);
  };
  var re = te("5.3.11"), oe = function () {
    function e(e2, t, n) {
      this.rules = e2, this.staticRulesId = "", this.isStatic = false, this.componentId = t, this.baseHash = ee(re, t), this.baseStyle = n, X.registerId(t);
    }

    return e.prototype.generateAndInjectStyles = function (e2, t, n) {
      var r2 = this.componentId, o = [];
      if (this.baseStyle && o.push(this.baseStyle.generateAndInjectStyles(e2, t, n)), this.isStatic && !n.hash)
        if (this.staticRulesId && t.hasNameForId(r2, this.staticRulesId))
          o.push(this.staticRulesId);
        else {
          var s2 = _e(this.rules, e2, t, n).join(""), i = Q(ee(this.baseHash, s2) >>> 0);
          if (!t.hasNameForId(r2, i)) {
            var a = n(s2, "." + i, void 0, r2);
            t.insertRules(r2, i, a);
          }
          o.push(i), this.staticRulesId = i;
        }
      else {
        for (var c2 = this.rules.length, u2 = ee(this.baseHash, n.hash), l = "", d = 0; d < c2; d++) {
          var h = this.rules[d];
          if ("string" == typeof h)
            l += h, u2 = ee(u2, h + d);
          else if (h) {
            var p = _e(h, e2, t, n), f = Array.isArray(p) ? p.join("") : p;
            u2 = ee(u2, f + d), l += f;
          }
        }
        if (l) {
          var m = Q(u2 >>> 0);
          if (!t.hasNameForId(r2, m)) {
            var y2 = n(l, "." + m, void 0, r2);
            t.insertRules(r2, m, y2);
          }
          o.push(m);
        }
      }
      return o.join(" ");
    }, e;
  }(), se = /^\s*\/\/.*$/gm, ie = [":", "[", ".", "#"];

  function ae(e) {
    var t, n, r2, o, s2 = void 0 === e ? w : e, i = s2.options, a = void 0 === i ? w : i, c2 = s2.plugins,
      u2 = void 0 === c2 ? S : c2, l = new stylis_min(a), d = [], p = function (e2) {
        function t2(t3) {
          if (t3)
            try {
              e2(t3 + "}");
            } catch (e3) {
            }
        }

        return function (n2, r3, o2, s3, i2, a2, c3, u3, l2, d2) {
          switch (n2) {
            case 1:
              if (0 === l2 && 64 === r3.charCodeAt(0))
                return e2(r3 + ";"), "";
              break;
            case 2:
              if (0 === u3)
                return r3 + "/*|*/";
              break;
            case 3:
              switch (u3) {
                case 102:
                case 112:
                  return e2(o2[0] + r3), "";
                default:
                  return r3 + (0 === d2 ? "/*|*/" : "");
              }
            case -2:
              r3.split("/*|*/}").forEach(t2);
          }
        };
      }(function (e2) {
        d.push(e2);
      }), f = function (e2, r3, s3) {
        return 0 === r3 && -1 !== ie.indexOf(s3[n.length]) || s3.match(o) ? e2 : "." + t;
      };

    function m(e2, s3, i2, a2) {
      void 0 === a2 && (a2 = "&");
      var c3 = e2.replace(se, ""), u3 = s3 && i2 ? i2 + " " + s3 + " { " + c3 + " }" : c3;
      return t = a2, n = s3, r2 = new RegExp("\\" + n + "\\b", "g"), o = new RegExp("(\\" + n + "\\b){2,}"), l(i2 || !s3 ? "" : s3, u3);
    }

    return l.use([].concat(u2, [function (e2, t2, o2) {
      2 === e2 && o2.length && o2[0].lastIndexOf(n) > 0 && (o2[0] = o2[0].replace(r2, f));
    }, p, function (e2) {
      if (-2 === e2) {
        var t2 = d;
        return d = [], t2;
      }
    }])), m.hash = u2.length ? u2.reduce(function (e2, t2) {
      return t2.name || D(15), ee(e2, t2.name);
    }, 5381).toString() : "", m;
  }

  var ce = r.createContext();
  ce.Consumer;
  var le = r.createContext(), de = (le.Consumer, new X()), he = ae();

  function pe() {
    return s(ce) || de;
  }

  function fe() {
    return s(le) || he;
  }

  var ye = function () {
    function e(e2, t) {
      var n = this;
      this.inject = function (e3, t2) {
        void 0 === t2 && (t2 = he);
        var r2 = n.name + t2.hash;
        e3.hasNameForId(n.id, r2) || e3.insertRules(n.id, r2, t2(n.rules, r2, "@keyframes"));
      }, this.toString = function () {
        return D(12, String(n.name));
      }, this.name = e2, this.id = "sc-keyframes-" + e2, this.rules = t;
    }

    return e.prototype.getName = function (e2) {
      return void 0 === e2 && (e2 = he), this.name + e2.hash;
    }, e;
  }(), ve = /([A-Z])/, ge = /([A-Z])/g, Se = /^ms-/, we = function (e) {
    return "-" + e.toLowerCase();
  };

  function Ee(e) {
    return ve.test(e) ? e.replace(ge, we).replace(Se, "-ms-") : e;
  }

  var be = function (e) {
    return null == e || false === e || "" === e;
  };

  function _e(e, n, r2, o) {
    if (Array.isArray(e)) {
      for (var s2, i = [], a = 0, c2 = e.length; a < c2; a += 1)
        "" !== (s2 = _e(e[a], n, r2, o)) && (Array.isArray(s2) ? i.push.apply(i, s2) : i.push(s2));
      return i;
    }
    if (be(e))
      return "";
    if (_(e))
      return "." + e.styledComponentId;
    if (E(e)) {
      if ("function" != typeof (l = e) || l.prototype && l.prototype.isReactComponent || !n)
        return e;
      var u2 = e(n);
      return reactIs$2.exports.isElement(u2) && console.warn(b(e) + " is not a styled component and cannot be referred to via component selector. See https://www.styled-components.com/docs/advanced#referring-to-other-components for more details."), _e(u2, n, r2, o);
    }
    var l;
    return e instanceof ye ? r2 ? (e.inject(r2, o), e.getName(o)) : e : g(e) ? function e2(t, n2) {
      var r3, o2, s3 = [];
      for (var i2 in t)
        t.hasOwnProperty(i2) && !be(t[i2]) && (Array.isArray(t[i2]) && t[i2].isCss || E(t[i2]) ? s3.push(Ee(i2) + ":", t[i2], ";") : g(t[i2]) ? s3.push.apply(s3, e2(t[i2], i2)) : s3.push(Ee(i2) + ": " + (r3 = i2, null == (o2 = t[i2]) || "boolean" == typeof o2 || "" === o2 ? "" : "number" != typeof o2 || 0 === o2 || r3 in unitlessKeys || r3.startsWith("--") ? String(o2).trim() : o2 + "px") + ";"));
      return n2 ? [n2 + " {"].concat(s3, ["}"]) : s3;
    }(e) : e.toString();
  }

  var Ne = function (e) {
    return Array.isArray(e) && (e.isCss = true), e;
  };

  function Ae(e) {
    for (var t = arguments.length, n = new Array(t > 1 ? t - 1 : 0), r2 = 1; r2 < t; r2++)
      n[r2 - 1] = arguments[r2];
    return E(e) || g(e) ? Ne(_e(v(S, [e].concat(n)))) : 0 === n.length && 1 === e.length && "string" == typeof e[0] ? e : Ne(_e(v(e, n)));
  }

  var Ce = /invalid hook call/i, Ie = /* @__PURE__ */ new Set(), Pe = function (e, t) {
    {
      var n = "The component " + e + (t ? ' with the id of "' + t + '"' : "") + " has been created dynamically.\nYou may see this warning because you've called styled inside another component.\nTo resolve this only create new StyledComponents outside of any render method and function component.",
        r2 = console.error;
      try {
        var o = true;
        console.error = function (e2) {
          if (Ce.test(e2))
            o = false, Ie.delete(n);
          else {
            for (var t2 = arguments.length, s2 = new Array(t2 > 1 ? t2 - 1 : 0), i = 1; i < t2; i++)
              s2[i - 1] = arguments[i];
            r2.apply(void 0, [e2].concat(s2));
          }
        }, c(), o && !Ie.has(n) && (console.warn(n), Ie.add(n));
      } catch (e2) {
        Ce.test(e2.message) && Ie.delete(n);
      } finally {
        console.error = r2;
      }
    }
  }, Oe = function (e, t, n) {
    return void 0 === n && (n = w), e.theme !== n.theme && e.theme || t || n.theme;
  }, Re = /[!"#$%&'()*+,./:;<=>?@[\\\]^`{|}~-]+/g, De = /(^-|-$)/g;

  function je(e) {
    return e.replace(Re, "-").replace(De, "");
  }

  var Te = function (e) {
    return Q(te(e) >>> 0);
  };

  function xe(e) {
    return "string" == typeof e && e.charAt(0) === e.charAt(0).toLowerCase();
  }

  var ke = function (e) {
    return "function" == typeof e || "object" == typeof e && null !== e && !Array.isArray(e);
  }, Ve = function (e) {
    return "__proto__" !== e && "constructor" !== e && "prototype" !== e;
  };

  function Be(e, t, n) {
    var r2 = e[n];
    ke(t) && ke(r2) ? ze(r2, t) : e[n] = t;
  }

  function ze(e) {
    for (var t = arguments.length, n = new Array(t > 1 ? t - 1 : 0), r2 = 1; r2 < t; r2++)
      n[r2 - 1] = arguments[r2];
    for (var o = 0, s2 = n; o < s2.length; o++) {
      var i = s2[o];
      if (ke(i))
        for (var a in i)
          Ve(a) && Be(e, i[a], a);
    }
    return e;
  }

  var Me = r.createContext();
  Me.Consumer;
  var Fe = {};

  function Ye(e, t, n) {
    var o = _(e), i = !xe(e), a = t.attrs, c2 = void 0 === a ? S : a, l = t.componentId,
      d = void 0 === l ? function (e2, t2) {
        var n2 = "string" != typeof e2 ? "sc" : je(e2);
        Fe[n2] = (Fe[n2] || 0) + 1;
        var r2 = n2 + "-" + Te("5.3.11" + n2 + Fe[n2]);
        return t2 ? t2 + "-" + r2 : r2;
      }(t.displayName, t.parentComponentId) : l, h = t.displayName, p = void 0 === h ? function (e2) {
        return xe(e2) ? "styled." + e2 : "Styled(" + b(e2) + ")";
      }(e) : h, v2 = t.displayName && t.componentId ? je(t.displayName) + "-" + t.componentId : t.componentId || d,
      g2 = o && e.attrs ? Array.prototype.concat(e.attrs, c2).filter(Boolean) : c2, N2 = t.shouldForwardProp;
    o && e.shouldForwardProp && (N2 = t.shouldForwardProp ? function (n2, r2, o2) {
      return e.shouldForwardProp(n2, r2, o2) && t.shouldForwardProp(n2, r2, o2);
    } : e.shouldForwardProp);
    var A, C2 = new oe(n, v2, o ? e.componentStyle : void 0), I2 = C2.isStatic && 0 === c2.length,
      P = function (e2, t2) {
        return function (e3, t3, n2, r2) {
          var o2 = e3.attrs, i2 = e3.componentStyle, a2 = e3.defaultProps, c3 = e3.foldedComponentIds,
            l2 = e3.shouldForwardProp, d2 = e3.styledComponentId, h2 = e3.target, p2 = function (e4, t4, n3) {
              void 0 === e4 && (e4 = w);
              var r3 = y({}, t4, {theme: e4}), o3 = {};
              return n3.forEach(function (e5) {
                var t5, n4, s2, i3 = e5;
                for (t5 in E(i3) && (i3 = i3(r3)), i3)
                  r3[t5] = o3[t5] = "className" === t5 ? (n4 = o3[t5], s2 = i3[t5], n4 && s2 ? n4 + " " + s2 : n4 || s2) : i3[t5];
              }), [r3, o3];
            }(Oe(t3, s(Me), a2) || w, t3, o2), m = p2[0], v3 = p2[1], g3 = function (e4, t4, n3, r3) {
              var o3 = pe(), s2 = fe(),
                i3 = t4 ? e4.generateAndInjectStyles(w, o3, s2) : e4.generateAndInjectStyles(n3, o3, s2);
              return !t4 && r3 && r3(i3), i3;
            }(i2, r2, m, e3.warnTooManyClasses), S2 = n2, b2 = v3.$as || t3.$as || v3.as || t3.as || h2, _2 = xe(b2),
            N3 = v3 !== t3 ? y({}, t3, {}, v3) : t3, A2 = {};
          for (var C3 in N3)
            "$" !== C3[0] && "as" !== C3 && ("forwardedAs" === C3 ? A2.as = N3[C3] : (l2 ? l2(C3, isPropValid, b2) : !_2 || isPropValid(C3)) && (A2[C3] = N3[C3]));
          return t3.style && v3.style !== t3.style && (A2.style = y({}, t3.style, {}, v3.style)), A2.className = Array.prototype.concat(c3, d2, g3 !== d2 ? g3 : null, t3.className, v3.className).filter(Boolean).join(" "), A2.ref = S2, u(b2, A2);
        }(A, e2, t2, I2);
      };
    return P.displayName = p, (A = r.forwardRef(P)).attrs = g2, A.componentStyle = C2, A.displayName = p, A.shouldForwardProp = N2, A.foldedComponentIds = o ? Array.prototype.concat(e.foldedComponentIds, e.styledComponentId) : S, A.styledComponentId = v2, A.target = o ? e.target : e, A.withComponent = function (e2) {
      var r2 = t.componentId, o2 = function (e3, t2) {
        if (null == e3)
          return {};
        var n2, r3, o3 = {}, s3 = Object.keys(e3);
        for (r3 = 0; r3 < s3.length; r3++)
          n2 = s3[r3], t2.indexOf(n2) >= 0 || (o3[n2] = e3[n2]);
        return o3;
      }(t, ["componentId"]), s2 = r2 && r2 + "-" + (xe(e2) ? e2 : je(b(e2)));
      return Ye(e2, y({}, o2, {attrs: g2, componentId: s2}), n);
    }, Object.defineProperty(A, "defaultProps", {
      get: function () {
        return this._foldedDefaultProps;
      }, set: function (t2) {
        this._foldedDefaultProps = o ? ze({}, e.defaultProps, t2) : t2;
      }
    }), Pe(p, v2), A.warnTooManyClasses = function (e2, t2) {
      var n2 = {}, r2 = false;
      return function (o2) {
        if (!r2 && (n2[o2] = true, Object.keys(n2).length >= 200)) {
          var s2 = t2 ? ' with the id of "' + t2 + '"' : "";
          console.warn("Over 200 classes were generated for component " + e2 + s2 + ".\nConsider using the attrs method, together with a style object for frequently changed styles.\nExample:\n  const Component = styled.div.attrs(props => ({\n    style: {\n      background: props.background,\n    },\n  }))`width: 100%;`\n\n  <Component />"), r2 = true, n2 = {};
        }
      };
    }(p, v2), Object.defineProperty(A, "toString", {
      value: function () {
        return "." + A.styledComponentId;
      }
    }), i && hoistNonReactStatics_cjs(A, e, {
      attrs: true,
      componentStyle: true,
      displayName: true,
      foldedComponentIds: true,
      shouldForwardProp: true,
      styledComponentId: true,
      target: true,
      withComponent: true
    }), A;
  }

  var qe = function (e) {
    return function e2(t, r2, o) {
      if (void 0 === o && (o = w), !reactIs$2.exports.isValidElementType(r2))
        return D(1, String(r2));
      var s2 = function () {
        return t(r2, o, Ae.apply(void 0, arguments));
      };
      return s2.withConfig = function (n) {
        return e2(t, r2, y({}, o, {}, n));
      }, s2.attrs = function (n) {
        return e2(t, r2, y({}, o, {attrs: Array.prototype.concat(o.attrs, n).filter(Boolean)}));
      }, s2;
    }(Ye, e);
  };
  ["a", "abbr", "address", "area", "article", "aside", "audio", "b", "base", "bdi", "bdo", "big", "blockquote", "body", "br", "button", "canvas", "caption", "cite", "code", "col", "colgroup", "data", "datalist", "dd", "del", "details", "dfn", "dialog", "div", "dl", "dt", "em", "embed", "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "head", "header", "hgroup", "hr", "html", "i", "iframe", "img", "input", "ins", "kbd", "keygen", "label", "legend", "li", "link", "main", "map", "mark", "marquee", "menu", "menuitem", "meta", "meter", "nav", "noscript", "object", "ol", "optgroup", "option", "output", "p", "param", "picture", "pre", "progress", "q", "rp", "rt", "ruby", "s", "samp", "script", "section", "select", "small", "source", "span", "strong", "style", "sub", "summary", "sup", "table", "tbody", "td", "textarea", "tfoot", "th", "thead", "time", "title", "tr", "track", "u", "ul", "var", "video", "wbr", "circle", "clipPath", "defs", "ellipse", "foreignObject", "g", "image", "line", "linearGradient", "marker", "mask", "path", "pattern", "polygon", "polyline", "radialGradient", "rect", "stop", "svg", "text", "textPath", "tspan"].forEach(function (e) {
    qe[e] = qe(e);
  });
  "undefined" != typeof navigator && "ReactNative" === navigator.product && console.warn("It looks like you've imported 'styled-components' on React Native.\nPerhaps you're looking to import 'styled-components/native'?\nRead more about this at https://www.styled-components.com/docs/basics#react-native"), "undefined" != typeof window && (window["__styled-components-init__"] = window["__styled-components-init__"] || 0, 1 === window["__styled-components-init__"] && console.warn("It looks like there are several instances of 'styled-components' initialized in this application. This may cause dynamic styles to not render properly, errors during the rehydration process, a missing theme prop, and makes your application bigger without good reason.\n\nSee https://s-c.sh/2BAXzed for more info."), window["__styled-components-init__"] += 1);
  const styled = qe;
  const modalStyle = {
    position: "absolute",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    width: 400,
    minWidth: 400,
    bgcolor: "background.paper",
    border: "2px solid #000",
    boxShadow: 24,
    p: 4
  };
  const wideModalStyle = {
    ...modalStyle,
    width: "50%"
  };
  const ButtonContainer = styled.div`
    display: flex;
    justify-content: space-between;
    flex-direction: row-reverse;
  `;
  const ErrorDiv = styled.div`
    color: red;
  `;
  const TooltipDiv = styled.div`
    color: var(--fo-palette-text-secondary);
  `;
  const ModalHeader = styled.h2`
    margin-top: 0;
  `;

  function fetchOrFail(input, init) {
    return fetch(
      input,
      init
    ).then((resp) => {
      if (!resp.ok) {
        return resp.text().then((text) => {
          return {success: false, val: text};
        });
      } else {
        return resp.json().then((json) => {
          return {success: true, val: json};
        });
      }
    }).then(({success, val}) => {
      if (success) {
        return val;
      } else {
        throw val;
      }
    });
  }

  function usePluginUrl() {
    const settings = usePluginSettings("dagshub", DefaultSettings());
    return (path) => {
      if (path.startsWith("/")) {
        path = path.slice(1);
      }
      return `${settings.server}/${path}`;
    };
  }

  const useRecoilValue$2 = window["recoil"].useRecoilValue;
  const fos$2 = window["__fos__"];
  const useState$2 = window["React"].useState;
  const Modal$2 = window["__mui__"].Modal;
  const Box$2 = window["__mui__"].Box;
  const Checkbox$1 = window["__mui__"].Checkbox;
  const FormGroup$1 = window["__mui__"].FormGroup;
  const FormControlLabel$1 = window["__mui__"].FormControlLabel;
  const TextField$1 = window["__mui__"].TextField;
  const Button$3 = window["__foc__"].Button;

  function SaveDatasetButton() {
    const filters = useRecoilValue$2(fos$2.filters);
    usePluginSettings("dagshub", DefaultSettings());
    const [modalOpen, setModalOpen] = useState$2(false);
    const [sending, setSending] = useState$2(false);
    const [errorText, setErrorText] = useState$2("");
    const [formState, setFormState] = useState$2({
      saveVoxelFilters: true
    });
    const pluginUrl = usePluginUrl();
    const requestData = () => {
      return JSON.stringify({
        ...formState,
        filters
      });
    };
    const saveDataset = () => {
      setSending(true);
      setErrorText("");
      fetch(pluginUrl("save_dataset"), {
        method: "POST",
        body: requestData()
      }).then((res) => {
        if (res.ok) {
          closeModal();
          return res.json();
        } else {
          throw res;
        }
      }).catch((err) => {
        err.text().then((text) => {
          setErrorText(text);
        });
      }).finally(() => {
        setSending(false);
      });
    };
    const closeModal = () => {
      setModalOpen(false);
    };
    const handleEvent = (isCheckbox) => {
      return (event) => {
        const val = isCheckbox ? event.target.checked : event.target.value;
        setFormState({
          ...formState,
          [event.target.name]: val
        });
      };
    };
    const canSubmit = () => {
      return !sending && !!formState.name;
    };
    const tooltipText = "Note: does not save limits, e.g. head()";
    return /* @__PURE__ */ jsxs(Fragment, {
      children: [/* @__PURE__ */ jsx(Button$3, {
        onClick: () => setModalOpen(true),
        children: "Save dataset"
      }), /* @__PURE__ */ jsx(Modal$2, {
        open: modalOpen,
        onClose: closeModal,
        children: /* @__PURE__ */ jsxs(Box$2, {
          sx: modalStyle,
          children: [/* @__PURE__ */ jsx(ModalHeader, {
            children: "Save dataset"
          }), /* @__PURE__ */ jsxs(FormGroup$1, {
            children: [/* @__PURE__ */ jsx(TextField$1, {
              label: "Dataset name",
              name: "name",
              value: formState.name,
              onChange: handleEvent(false)
            }), /* @__PURE__ */ jsx(FormControlLabel$1, {
              control: /* @__PURE__ */ jsx(Checkbox$1, {
                checked: formState.saveVoxelFilters,
                name: "saveVoxelFilters",
                onChange: handleEvent(true)
              }),
              label: "Include current FiftyOne filters"
            }), /* @__PURE__ */ jsx(TooltipDiv, {
              children: tooltipText
            }), /* @__PURE__ */ jsxs(ButtonContainer, {
              children: [/* @__PURE__ */ jsx(Button$3, {
                onClick: saveDataset,
                disabled: !canSubmit(),
                children: "Save!"
              }), errorText && /* @__PURE__ */ jsx(ErrorDiv, {
                children: errorText
              })]
            })]
          })]
        })
      })]
    });
  }

  const atom = window["recoil"].atom;
  const metadataFields = atom({
    key: "__dagshub__fields",
    default: []
  });
  var MetadataFieldType = /* @__PURE__ */ ((MetadataFieldType2) => {
    MetadataFieldType2["BOOLEAN"] = "BOOLEAN";
    MetadataFieldType2["INTEGER"] = "INTEGER";
    MetadataFieldType2["FLOAT"] = "FLOAT";
    MetadataFieldType2["STRING"] = "STRING";
    MetadataFieldType2["BLOB"] = "BLOB";
    return MetadataFieldType2;
  })(MetadataFieldType || {});
  const MAX_STRING_LENGTH = 500;

  function validateFieldValue(field, value) {
    if (field == "INTEGER" || field == "FLOAT") {
      const num = Number(value);
      if (Number.isNaN(num)) {
        throw new Error(`Not a valid number`);
      }
      if (field == "INTEGER" && !Number.isInteger(num)) {
        throw new Error(`Not a valid integer`);
      }
      return num;
    }
    if (field == "BOOLEAN") {
      if (typeof value !== "boolean") {
        throw new Error(`Not a valid boolean`);
      }
      return value;
    }
    if (field == "STRING") {
      if (typeof value !== "string") {
        throw new Error(`Not a string`);
      }
      if (value.length > MAX_STRING_LENGTH) {
        throw new Error(`Bigger than the maximum length of ${MAX_STRING_LENGTH}`);
      }
    }
    return value;
  }

  const useState$1 = window["React"].useState;
  const useCallback = window["React"].useCallback;
  const createContext = window["React"].createContext;
  const useContext = window["React"].useContext;
  const Box$1 = window["__mui__"].Box;
  const Modal$1 = window["__mui__"].Modal;
  const Button$2 = window["__foc__"].Button;
  const ErrorContext = createContext(null);
  const ErrorModalProvider = (props) => {
    const [errorText, setErrorText] = useState$1();
    const unSetModal = useCallback(() => {
      setErrorText(void 0);
    }, [setErrorText]);
    return /* @__PURE__ */ jsxs(ErrorContext.Provider, {
      value: {
        unSetModal,
        setErrorText
      },
      ...props,
      children: [errorText && /* @__PURE__ */ jsx(ErrorModal, {
        errorText,
        unSetModal
      }), props.children]
    });
  };
  const ErrorModal = ({
                        errorText,
                        unSetModal
                      }) => {
    const onClose = () => {
      unSetModal();
    };
    if (!!errorText) {
      console.log("SHOWING MODAL", errorText);
    }
    return /* @__PURE__ */ jsx(Modal$1, {
      onClose,
      open: errorText !== void 0,
      children: /* @__PURE__ */ jsxs(Box$1, {
        sx: wideModalStyle,
        children: [/* @__PURE__ */ jsx(ModalHeader, {
          children: "Error"
        }), /* @__PURE__ */ jsx(Box$1, {
          component: "pre",
          sx: {
            overflowX: "auto",
            overflowY: "auto",
            fontFamily: "Monospace",
            background: "var(--fo-palette-background-level1)",
            maxHeight: "50vh",
            padding: "15px"
          },
          children: errorText
        }), /* @__PURE__ */ jsx(Button$2, {
          onClick: onClose,
          children: "Close"
        })]
      })
    });
  };
  const useErrorModal = () => {
    const context = useContext(ErrorContext);
    if (context === void 0) {
      throw new Error("useModal must be used within a UserProvider");
    }
    return context.setErrorText;
  };
  const Button$1 = window["__foc__"].Button;
  const Autocomplete = window["__mui__"].Autocomplete;
  const Box = window["__mui__"].Box;
  const Checkbox = window["__mui__"].Checkbox;
  const FormControlLabel = window["__mui__"].FormControlLabel;
  const FormGroup = window["__mui__"].FormGroup;
  const Grid = window["__mui__"].Grid;
  const Modal = window["__mui__"].Modal;
  const TextField = window["__mui__"].TextField;
  const useEffect = window["React"].useEffect;
  const useState = window["React"].useState;
  const useRecoilState = window["recoil"].useRecoilState;
  const useRecoilValue$1 = window["recoil"].useRecoilValue;
  const fos$1 = window["__fos__"];
  const SubmitButtonContainer = styled.div`
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
  `;
  const FieldPlaceholder = styled(TooltipDiv)`
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
  `;

  function UpdateMetadataButton() {
    const selected = useRecoilValue$1(fos$1.selectedSamples);
    const [modalOpen, setModalOpen] = useState(false);
    useState(false);
    useState("");
    usePluginSettings("dagshub", DefaultSettings());
    const [fieldValue, setFieldValue] = useState(void 0);
    const [selectedField, setSelectedField] = useState(null);
    const [validationError, setValidationError] = useState(null);
    const setErrorModal = useErrorModal();
    const closeModal = () => {
      setModalOpen(false);
    };
    const [fields, setFields] = useRecoilState(metadataFields);
    const pluginUrl = usePluginUrl();
    const raiseError = (res) => {
      console.error("ERRROR:", res);
      setErrorModal(res);
    };
    const fetchFields = () => {
      if (!fields.length) {
        fetchOrFail(pluginUrl("datasource/fields")).then((res) => {
          setFields(res.map((a) => JSON.parse(a)));
        }).catch((res) => raiseError(res));
      }
    };
    useEffect(fetchFields, []);
    fields.map((s2, i) => /* @__PURE__ */ jsx("div", {
      children: s2.name
    }, i));
    fields.map((s2) => s2.name);
    const selectedFieldChanged = (event, newValue) => {
      console.log("Set selected to", newValue);
      setSelectedField(newValue);
      setValidationError(null);
      if (newValue !== null && newValue.valueType == MetadataFieldType.BOOLEAN) {
        setFieldValue(false);
      } else {
        setFieldValue(void 0);
      }
    };
    const fieldValueChanged = (val) => {
      setFieldValue(val);
    };
    const fieldStyle = {
      flexGrow: 1,
      width: "100%",
      height: "100%"
    };
    const updateMetadata = () => {
      console.log("UPDATING");
      setValidationError(null);
      let val = null;
      try {
        val = validateFieldValue(selectedField.valueType, fieldValue);
      } catch (error) {
        setValidationError(error.message);
        return;
      }
      const requestData = {
        field: selectedField,
        value: val
      };
      fetchOrFail(pluginUrl("datasource/update_metadata"), {
        method: "POST",
        body: JSON.stringify(requestData)
      }).then((res) => console.log(res)).catch((res) => raiseError(res));
      console.log(val);
    };
    const canSubmit = () => {
      return fieldValue !== void 0;
    };
    let fieldEdit;
    if (!selectedField) {
      fieldEdit = /* @__PURE__ */ jsx(FieldPlaceholder, {
        children: "Choose a field"
      });
    } else if (selectedField.valueType == MetadataFieldType.BOOLEAN) {
      fieldEdit = /* @__PURE__ */ jsx(FormControlLabel, {
        control: /* @__PURE__ */ jsx(Checkbox, {
          onChange: (ev) => fieldValueChanged(ev.target.checked)
        }),
        label: "Value",
        style: fieldStyle
      });
    } else {
      fieldEdit = /* @__PURE__ */ jsx(TextField, {
        error: validationError !== null,
        helperText: validationError,
        onChange: (ev) => fieldValueChanged(ev.target.value),
        label: "Value",
        style: fieldStyle
      });
    }
    return /* @__PURE__ */ jsxs(Fragment, {
      children: [/* @__PURE__ */ jsx(Button$1, {
        onClick: () => setModalOpen(true),
        children: "Update metadata for selected"
      }), /* @__PURE__ */ jsx(Modal, {
        open: modalOpen,
        onClose: closeModal,
        children: /* @__PURE__ */ jsxs(Box, {
          sx: wideModalStyle,
          children: [/* @__PURE__ */ jsx(ModalHeader, {
            children: "Update metadata for selected samples"
          }), /* @__PURE__ */ jsxs(FormGroup, {
            children: [/* @__PURE__ */ jsxs(TooltipDiv, {
              children: ["Currently ", selected.size, " sample(s) are selected"]
            }), /* @__PURE__ */ jsxs(Grid, {
              container: true,
              spacing: 2,
              children: [/* @__PURE__ */ jsx(Grid, {
                item: true,
                xs: 6,
                children: /* @__PURE__ */ jsx(Autocomplete, {
                  options: fields,
                  getOptionLabel: (option) => option.name,
                  renderInput: (params) => /* @__PURE__ */ jsx(TextField, {
                    ...params,
                    label: "Field"
                  }),
                  onChange: selectedFieldChanged,
                  style: fieldStyle
                })
              }), /* @__PURE__ */ jsx(Grid, {
                item: true,
                xs: 6,
                children: fieldEdit
              })]
            }), /* @__PURE__ */ jsx(SubmitButtonContainer, {
              children: /* @__PURE__ */ jsx(Button$1, {
                onClick: updateMetadata,
                disabled: !canSubmit(),
                children: "Save!"
              })
            })]
          })]
        })
      })]
    });
  }

  const fos = window["__fos__"];
  const useRecoilValue = window["recoil"].useRecoilValue;
  const Button = window["__foc__"].Button;
  const Card = window["__mui__"].Card;
  const CardContent = window["__mui__"].CardContent;
  const CardHeader = window["__mui__"].CardHeader;
  const CardStack = styled.div`
    display: flex;
    flex-direction: row;
    gap: 16px;
    flex-wrap: wrap;
    padding: 16px;
  `;
  const ActionsCard = styled(Card)`
    min-width: 300px;
  `;

  function Plugin() {
    useRecoilValue(fos.dataset);
    useRecoilValue(fos.view);
    useRecoilValue(fos.filters);
    const settings = usePluginSettings("dagshub", DefaultSettings());
    const toLabelStudio = () => {
      fetch(`${settings.server}/labelstudio`, {
        method: "POST"
      }).then((res) => {
        if (res.ok) {
          return res.json();
        } else {
          throw res;
        }
      }).then((res) => {
        console.log("Need to open link", res["link"]);
        window.open(res["link"], "_blank").focus();
      }).catch((errResp) => {
        errResp.content().then((text) => {
          console.error("Error while sending annotation to labelstudio", text);
        });
      });
    };
    return /* @__PURE__ */ jsx(Fragment, {
      children: /* @__PURE__ */ jsx(ErrorModalProvider, {
        children: /* @__PURE__ */ jsxs(CardStack, {
          children: [/* @__PURE__ */ jsxs(ActionsCard, {
            raised: true,
            children: [/* @__PURE__ */ jsx(CardHeader, {
              title: "Metadata"
            }), /* @__PURE__ */ jsx(CardContent, {
              children: /* @__PURE__ */ jsx(UpdateMetadataButton, {})
            })]
          }), /* @__PURE__ */ jsxs(ActionsCard, {
            raised: true,
            children: [/* @__PURE__ */ jsx(CardHeader, {
              title: "Dataset"
            }), /* @__PURE__ */ jsx(CardContent, {
              children: /* @__PURE__ */ jsx(SaveDatasetButton, {})
            })]
          }), /* @__PURE__ */ jsxs(ActionsCard, {
            raised: true,
            children: [/* @__PURE__ */ jsx(CardHeader, {
              title: "Annotations"
            }), /* @__PURE__ */ jsx(CardContent, {
              children: /* @__PURE__ */ jsx(Button, {
                onClick: toLabelStudio,
                children: "Annotate selected in LabelStudio"
              })
            })]
          })]
        })
      })
    });
  }

  const DagsHubIcon = () => {
    return /* @__PURE__ */ jsxs("svg", {
      width: "1rem",
      height: "1rem",
      viewBox: "0 -10 260 260",
      fill: "none",
      xmlns: "http://www.w3.org/2000/svg",
      style: {
        marginRight: "0.5rem"
      },
      children: [/* @__PURE__ */ jsxs("mask", {
        id: "path-1-outside-1_604_2",
        maskUnits: "userSpaceOnUse",
        x: "0",
        y: "0",
        width: "262",
        height: "233",
        fill: "black",
        children: [/* @__PURE__ */ jsx("rect", {
          fill: "white",
          width: "262",
          height: "233"
        }), /* @__PURE__ */ jsx("path", {
          "fill-rule": "evenodd",
          "clip-rule": "evenodd",
          d: "M255.982 28.1241L255.935 27.2728C255.935 26.8944 255.887 26.2796 255.793 25.381C255.752 24.8902 255.675 24.3995 255.594 23.8782L255.556 23.631V23.5837C255.414 22.6378 255.177 21.6919 254.845 20.746L254.324 19.5164C254.087 19.0434 253.85 18.5705 253.566 18.1448C252.997 17.2462 252.286 16.4422 251.433 15.78C250.296 14.8341 248.922 14.172 247.453 13.8409C246.884 13.6991 246.316 13.6518 245.747 13.6045L245.084 13.5572H243.947C243.236 13.5572 242.525 13.6518 241.814 13.7464C241.104 13.8409 240.345 14.0301 239.635 14.2193L238.971 14.4085C238.118 14.6923 237.313 15.0233 236.555 15.4017C233.238 17.057 230.537 19.5637 228.547 21.5501C227.9 22.1953 227.254 22.8846 226.622 23.5579C226.329 23.8712 226.037 24.1821 225.751 24.4823C225.056 25.2391 224.319 25.9959 223.582 26.7527C223.213 27.131 222.845 27.5093 222.482 27.8876C220.586 29.7794 218.549 31.482 216.369 32.9955C214.284 34.4143 212.057 35.5494 209.688 36.4007L205.092 38.1506L204.76 38.2925C204.239 38.529 203.718 38.7655 203.244 39.0019L202.486 39.3803L201.964 39.6168C201.348 39.9006 200.732 40.2316 200.164 40.5627C197.652 41.9342 195.236 43.495 192.914 45.1976L192.867 45.2449L192.061 45.8597C191.492 46.2854 190.924 46.711 190.403 47.184L188.081 49.1704L186.47 50.6838C183.721 53.2378 181.352 56.1228 179.41 59.2915C179.291 59.4807 179.173 59.6817 179.054 59.8827C178.936 60.0837 178.817 60.2848 178.699 60.4739L178.13 60.2374C172.823 58.2983 167.421 56.7376 161.925 55.5079C150.695 53.0486 139.18 52.1027 127.666 52.8121C126.766 52.8594 125.913 52.9067 125.06 53.0013C124.681 53.0486 124.302 53.0959 123.923 53.0959L122.501 53.2378L121.98 53.2851L120.322 53.4743C119.563 53.5688 118.805 53.6634 118.142 53.758L117.052 53.8999C114.92 54.231 113.451 54.4674 112.408 54.7039C109.092 55.3188 105.822 56.312 102.695 57.6362C101.605 55.2242 100.231 52.954 98.5723 50.873C97.4824 49.4542 96.2978 48.1299 95.0185 46.8529C94.1656 46.0016 93.2652 45.1503 92.2228 44.2517L91.5594 43.7315C91.3916 43.6059 91.2332 43.4803 91.0798 43.3588C90.8868 43.2058 90.7018 43.0592 90.517 42.9274L90.1379 42.6437L89.9484 42.5005C89.6045 42.2399 89.1938 41.9285 88.7164 41.6505L88.4321 41.4613C87.9582 41.1302 87.437 40.7992 86.821 40.4208L86.7736 40.3735C86.6224 40.2854 86.4644 40.1907 86.2997 40.0919C85.8454 39.8193 85.34 39.5161 84.7835 39.2384L83.8358 38.7655C83.5515 38.6236 83.2672 38.4817 82.9829 38.3871L81.7035 37.8196L79.3817 36.921L76.0648 35.8332L75.2119 35.5494C74.2642 35.2656 73.4113 34.9819 72.6532 34.6981H72.6058L71.8476 34.4143L70.8526 34.036L69.1467 33.2319C67.0144 32.286 64.9769 31.151 63.0342 29.7794L62.9868 29.7321C60.9019 28.2187 58.9592 26.6106 57.0638 24.8607L55.2632 23.2527C54.8523 22.881 54.4378 22.5023 54.0199 22.1204C52.896 21.0935 51.7464 20.0431 50.5722 19.0434C48.1082 16.9151 45.7864 15.1652 43.6067 13.6518C41.2849 11.9491 38.8209 10.4357 36.2622 9.15873C34.9354 8.4966 33.6087 7.88177 32.2345 7.40882L32.0924 7.36152C30.6235 6.84127 29.1072 6.46291 27.5435 6.22644C25.8377 5.94267 24.1318 5.94267 22.426 6.13185C20.6728 6.32103 18.967 6.84127 17.4033 7.5507L17.3085 7.598C15.9344 8.26013 14.655 9.15874 13.4704 10.1992L13.3757 10.2938C12.9492 10.7195 12.5227 11.1451 12.0963 11.6181L11.812 11.9964C11.5277 12.3275 11.2908 12.6586 11.0538 12.9896C10.2483 14.1247 9.53755 15.3544 8.96894 16.6314L8.54248 17.5773C8.4951 17.6955 8.45956 17.8019 8.42994 17.8906C8.40033 17.9793 8.37664 18.0502 8.35294 18.0975C8.32366 18.156 8.25818 18.3409 8.16769 18.5964C8.11176 18.7544 8.04627 18.9393 7.97387 19.138L7.92649 19.2799C7.54742 20.3677 7.26311 21.5028 7.02619 22.6378C6.6945 24.2932 6.4102 25.9958 6.22066 27.6984L6.17328 28.1714C6.14885 28.3421 6.13701 28.5253 6.12478 28.7147C6.1133 28.8926 6.10146 29.0759 6.07851 29.2592L6.03112 30.7726C5.98374 31.9077 5.98374 32.9955 6.07851 34.1306L6.12589 34.7927C6.4102 37.6304 7.02619 40.4208 7.92649 43.1639C8.70904 45.4153 9.67046 47.622 10.5935 49.7407L10.6748 49.9271L10.9591 50.6365C12.0015 52.954 12.8544 55.2242 13.66 57.4943L13.9443 58.2983C14.0455 58.6352 14.1528 58.96 14.2575 59.2771C14.4468 59.8505 14.6278 60.3987 14.7498 60.9469V61.0415L14.9867 61.7982C15.0341 61.9637 15.0815 62.1411 15.1289 62.3184C15.1763 62.4958 15.2236 62.6731 15.271 62.8387L15.7449 64.8251L15.7922 64.967C15.9818 65.7237 16.1713 66.6223 16.3135 67.5682L16.503 68.7033L16.6925 69.6492C16.6925 69.7201 16.7044 69.7911 16.7162 69.862C16.7281 69.9329 16.7399 70.0039 16.7399 70.0748L17.4033 74.757V74.8989C17.427 74.9935 17.4388 75.0999 17.4507 75.2064C17.4625 75.3128 17.4744 75.4192 17.4981 75.5138C17.5241 75.6698 17.5502 75.833 17.5772 76.0023C17.6485 76.449 17.7267 76.9385 17.8298 77.4529L17.9719 78.115C18.0667 78.6825 18.2088 79.2974 18.3984 79.9595C18.4458 80.196 18.4931 80.4325 18.5879 80.6216C18.73 81.1891 18.8722 81.7093 19.0143 82.2295C19.962 85.3982 21.194 88.4726 22.7103 91.4049C23.3722 92.7262 24.0341 93.8672 24.6644 94.9539L24.9374 95.425C25.1283 95.7517 25.3349 96.0784 25.5301 96.387C25.674 96.6146 25.8118 96.8323 25.9324 97.033L27.3066 99.114C28.6807 101.148 30.197 103.087 31.8081 104.931C33.0401 106.397 34.0825 107.533 35.0776 108.526L35.125 108.573C37.2099 110.749 39.5317 112.688 41.9957 114.438L41.7959 115.032C41.5325 115.813 41.2751 116.577 41.048 117.37C40.1003 120.775 39.4843 124.275 39.2474 127.775L39.2 128.106L39.1508 128.75C39.0479 130.083 38.887 132.166 38.7262 135.579C38.5366 139.599 38.5366 145.983 38.8209 151.281C38.9631 153.74 39.1526 156.247 39.3895 158.327C39.4193 158.743 39.4677 159.121 39.5113 159.462C39.5372 159.665 39.5614 159.854 39.5791 160.03L40.0529 163.766V163.814C40.2424 165.185 40.6215 167.361 41.1427 169.962C41.664 172.563 42.3273 175.212 43.0855 177.718C43.9858 180.793 44.9335 183.299 45.5495 184.907C46.4971 187.319 47.587 189.684 48.819 192.002C49.0917 192.546 49.3645 192.995 49.6109 193.4L49.7666 193.657C49.814 193.752 49.8733 193.846 49.9325 193.941C49.9917 194.035 50.051 194.13 50.0983 194.224L51.1408 195.974L51.1882 196.069C53.2731 199.38 55.8792 202.312 58.9592 204.771C60.1911 205.765 61.5179 206.616 62.892 207.42C62.9631 207.514 63.0223 207.609 63.0815 207.703C63.1407 207.798 63.2 207.893 63.2711 207.987C64.2662 209.406 65.356 210.73 66.5406 211.913C67.7252 213.048 68.9572 214.136 70.284 215.082L70.3787 215.129C71.6581 216.028 73.0322 216.832 74.4538 217.541C79.1922 219.906 84.594 221.419 90.896 222.081C93.4548 222.365 96.0609 222.507 98.667 222.507H98.7618C101.273 222.507 103.832 222.318 106.343 222.034H106.391C108.76 221.75 111.176 221.325 113.498 220.757C114.195 220.611 114.834 220.436 115.417 220.277C115.588 220.23 115.754 220.185 115.915 220.142L116.768 219.906L117.052 219.811L117.858 219.575C118.616 219.338 119.374 219.102 120.227 218.818C120.843 218.581 121.459 218.345 122.122 218.109C122.501 218.44 122.833 218.723 123.259 219.054L123.307 219.102C125.723 220.994 128.377 222.507 131.22 223.595C131.789 223.831 132.452 224.068 133.494 224.399C133.755 224.493 134.016 224.576 134.276 224.659C134.537 224.742 134.797 224.824 135.058 224.919L135.295 225.014C135.773 225.163 136.271 225.293 136.787 225.429C137.088 225.508 137.397 225.589 137.712 225.676C138.205 225.817 138.673 225.905 139.173 226C139.345 226.032 139.52 226.065 139.702 226.101L140.507 226.243L140.697 226.291C141.076 226.338 141.455 226.385 141.834 226.48L143.066 226.669L145.483 226.905H145.625C145.828 226.905 146.017 226.919 146.193 226.932C146.345 226.943 146.488 226.953 146.62 226.953L148.326 227H149.747C150.221 227 150.884 227 151.642 226.953C153.68 226.811 155.67 226.574 157.66 226.149L159.271 225.818L159.413 225.77C159.84 225.676 160.219 225.581 160.598 225.439L160.977 225.345L162.02 225.061L163.82 224.493L164.436 224.304C164.616 224.233 164.795 224.168 164.977 224.102C165.275 223.994 165.581 223.883 165.905 223.737L167.137 223.216C167.99 222.885 168.795 222.46 169.601 222.034C170.217 221.703 170.833 221.372 171.402 221.041L171.591 220.946C172.728 220.237 173.818 219.433 174.861 218.581L175.145 218.345C175.287 218.203 175.441 218.073 175.595 217.943C175.749 217.813 175.903 217.683 176.045 217.541C177.751 218.203 179.457 218.771 181.163 219.244C186.091 220.71 191.208 221.608 196.326 221.939C202.012 222.318 207.745 221.703 213.242 220.142C216.274 219.244 219.165 217.919 221.818 216.217C224.709 214.372 227.22 212.007 229.21 209.264L229.258 209.217C230.253 207.798 231.106 206.332 231.864 204.771C233.238 201.744 234.043 198.528 234.328 195.265C234.47 193.988 234.517 192.758 234.47 191.481V190.488C234.423 189.827 234.375 189.307 234.328 188.787C234.328 188.686 234.314 188.583 234.301 188.489C234.291 188.407 234.28 188.331 234.28 188.265L234.138 186.941L233.854 185.617C233.83 185.522 233.818 185.439 233.806 185.357C233.795 185.274 233.783 185.191 233.759 185.097C233.664 184.624 233.522 184.009 233.333 183.347L232.764 181.502C232.622 180.982 232.432 180.509 232.195 180.036L231.437 178.239C231.248 177.813 231.106 177.529 230.963 177.246L230.537 176.489C230.443 176.319 230.356 176.15 230.27 175.983C230.142 175.732 230.016 175.487 229.874 175.259L228.736 173.415L228.642 173.273C227.741 171.901 226.794 170.672 225.846 169.442L227.125 167.597C229.115 164.381 230.632 160.929 231.674 157.287L231.864 156.578C232.859 152.889 233.617 149.152 234.091 145.369V145.274L234.186 144.47C234.28 143.855 234.375 143.193 234.422 142.484L234.659 139.788L234.707 138.984C234.802 137.234 234.896 135.437 234.849 133.45C234.802 129.052 234.422 124.653 233.712 120.302C233.238 117.512 232.574 114.721 231.769 111.978C232.622 111.174 233.427 110.323 234.186 109.424C236.602 106.492 238.592 103.276 240.061 99.8235C241.009 97.7425 242.43 94.3372 244.326 88.9456C246.221 83.5539 248.069 77.2637 249.68 70.8789C251.291 64.494 252.76 57.6835 253.803 51.346C254.798 45.5287 255.508 39.806 255.84 35.3129C255.982 32.9009 256.03 30.5361 255.982 28.1241Z"
        })]
      }), /* @__PURE__ */ jsx("path", {
        "fill-rule": "evenodd",
        "clip-rule": "evenodd",
        d: "M255.982 28.1241L255.935 27.2728C255.935 26.8944 255.887 26.2796 255.793 25.381C255.752 24.8902 255.675 24.3995 255.594 23.8782L255.556 23.631V23.5837C255.414 22.6378 255.177 21.6919 254.845 20.746L254.324 19.5164C254.087 19.0434 253.85 18.5705 253.566 18.1448C252.997 17.2462 252.286 16.4422 251.433 15.78C250.296 14.8341 248.922 14.172 247.453 13.8409C246.884 13.6991 246.316 13.6518 245.747 13.6045L245.084 13.5572H243.947C243.236 13.5572 242.525 13.6518 241.814 13.7464C241.104 13.8409 240.345 14.0301 239.635 14.2193L238.971 14.4085C238.118 14.6923 237.313 15.0233 236.555 15.4017C233.238 17.057 230.537 19.5637 228.547 21.5501C227.9 22.1953 227.254 22.8846 226.622 23.5579C226.329 23.8712 226.037 24.1821 225.751 24.4823C225.056 25.2391 224.319 25.9959 223.582 26.7527C223.213 27.131 222.845 27.5093 222.482 27.8876C220.586 29.7794 218.549 31.482 216.369 32.9955C214.284 34.4143 212.057 35.5494 209.688 36.4007L205.092 38.1506L204.76 38.2925C204.239 38.529 203.718 38.7655 203.244 39.0019L202.486 39.3803L201.964 39.6168C201.348 39.9006 200.732 40.2316 200.164 40.5627C197.652 41.9342 195.236 43.495 192.914 45.1976L192.867 45.2449L192.061 45.8597C191.492 46.2854 190.924 46.711 190.403 47.184L188.081 49.1704L186.47 50.6838C183.721 53.2378 181.352 56.1228 179.41 59.2915C179.291 59.4807 179.173 59.6817 179.054 59.8827C178.936 60.0837 178.817 60.2848 178.699 60.4739L178.13 60.2374C172.823 58.2983 167.421 56.7376 161.925 55.5079C150.695 53.0486 139.18 52.1027 127.666 52.8121C126.766 52.8594 125.913 52.9067 125.06 53.0013C124.681 53.0486 124.302 53.0959 123.923 53.0959L122.501 53.2378L121.98 53.2851L120.322 53.4743C119.563 53.5688 118.805 53.6634 118.142 53.758L117.052 53.8999C114.92 54.231 113.451 54.4674 112.408 54.7039C109.092 55.3188 105.822 56.312 102.695 57.6362C101.605 55.2242 100.231 52.954 98.5723 50.873C97.4824 49.4542 96.2978 48.1299 95.0185 46.8529C94.1656 46.0016 93.2652 45.1503 92.2228 44.2517L91.5594 43.7315C91.3916 43.6059 91.2332 43.4803 91.0798 43.3588C90.8868 43.2058 90.7018 43.0592 90.517 42.9274L90.1379 42.6437L89.9484 42.5005C89.6045 42.2399 89.1938 41.9285 88.7164 41.6505L88.4321 41.4613C87.9582 41.1302 87.437 40.7992 86.821 40.4208L86.7736 40.3735C86.6224 40.2854 86.4644 40.1907 86.2997 40.0919C85.8454 39.8193 85.34 39.5161 84.7835 39.2384L83.8358 38.7655C83.5515 38.6236 83.2672 38.4817 82.9829 38.3871L81.7035 37.8196L79.3817 36.921L76.0648 35.8332L75.2119 35.5494C74.2642 35.2656 73.4113 34.9819 72.6532 34.6981H72.6058L71.8476 34.4143L70.8526 34.036L69.1467 33.2319C67.0144 32.286 64.9769 31.151 63.0342 29.7794L62.9868 29.7321C60.9019 28.2187 58.9592 26.6106 57.0638 24.8607L55.2632 23.2527C54.8523 22.881 54.4378 22.5023 54.0199 22.1204C52.896 21.0935 51.7464 20.0431 50.5722 19.0434C48.1082 16.9151 45.7864 15.1652 43.6067 13.6518C41.2849 11.9491 38.8209 10.4357 36.2622 9.15873C34.9354 8.4966 33.6087 7.88177 32.2345 7.40882L32.0924 7.36152C30.6235 6.84127 29.1072 6.46291 27.5435 6.22644C25.8377 5.94267 24.1318 5.94267 22.426 6.13185C20.6728 6.32103 18.967 6.84127 17.4033 7.5507L17.3085 7.598C15.9344 8.26013 14.655 9.15874 13.4704 10.1992L13.3757 10.2938C12.9492 10.7195 12.5227 11.1451 12.0963 11.6181L11.812 11.9964C11.5277 12.3275 11.2908 12.6586 11.0538 12.9896C10.2483 14.1247 9.53755 15.3544 8.96894 16.6314L8.54248 17.5773C8.4951 17.6955 8.45956 17.8019 8.42994 17.8906C8.40033 17.9793 8.37664 18.0502 8.35294 18.0975C8.32366 18.156 8.25818 18.3409 8.16769 18.5964C8.11176 18.7544 8.04627 18.9393 7.97387 19.138L7.92649 19.2799C7.54742 20.3677 7.26311 21.5028 7.02619 22.6378C6.6945 24.2932 6.4102 25.9958 6.22066 27.6984L6.17328 28.1714C6.14885 28.3421 6.13701 28.5253 6.12478 28.7147C6.1133 28.8926 6.10146 29.0759 6.07851 29.2592L6.03112 30.7726C5.98374 31.9077 5.98374 32.9955 6.07851 34.1306L6.12589 34.7927C6.4102 37.6304 7.02619 40.4208 7.92649 43.1639C8.70904 45.4153 9.67046 47.622 10.5935 49.7407L10.6748 49.9271L10.9591 50.6365C12.0015 52.954 12.8544 55.2242 13.66 57.4943L13.9443 58.2983C14.0455 58.6352 14.1528 58.96 14.2575 59.2771C14.4468 59.8505 14.6278 60.3987 14.7498 60.9469V61.0415L14.9867 61.7982C15.0341 61.9637 15.0815 62.1411 15.1289 62.3184C15.1763 62.4958 15.2236 62.6731 15.271 62.8387L15.7449 64.8251L15.7922 64.967C15.9818 65.7237 16.1713 66.6223 16.3135 67.5682L16.503 68.7033L16.6925 69.6492C16.6925 69.7201 16.7044 69.7911 16.7162 69.862C16.7281 69.9329 16.7399 70.0039 16.7399 70.0748L17.4033 74.757V74.8989C17.427 74.9935 17.4388 75.0999 17.4507 75.2064C17.4625 75.3128 17.4744 75.4192 17.4981 75.5138C17.5241 75.6698 17.5502 75.833 17.5772 76.0023C17.6485 76.449 17.7267 76.9385 17.8298 77.4529L17.9719 78.115C18.0667 78.6825 18.2088 79.2974 18.3984 79.9595C18.4458 80.196 18.4931 80.4325 18.5879 80.6216C18.73 81.1891 18.8722 81.7093 19.0143 82.2295C19.962 85.3982 21.194 88.4726 22.7103 91.4049C23.3722 92.7262 24.0341 93.8672 24.6644 94.9539L24.9374 95.425C25.1283 95.7517 25.3349 96.0784 25.5301 96.387C25.674 96.6146 25.8118 96.8323 25.9324 97.033L27.3066 99.114C28.6807 101.148 30.197 103.087 31.8081 104.931C33.0401 106.397 34.0825 107.533 35.0776 108.526L35.125 108.573C37.2099 110.749 39.5317 112.688 41.9957 114.438L41.7959 115.032C41.5325 115.813 41.2751 116.577 41.048 117.37C40.1003 120.775 39.4843 124.275 39.2474 127.775L39.2 128.106L39.1508 128.75C39.0479 130.083 38.887 132.166 38.7262 135.579C38.5366 139.599 38.5366 145.983 38.8209 151.281C38.9631 153.74 39.1526 156.247 39.3895 158.327C39.4193 158.743 39.4677 159.121 39.5113 159.462C39.5372 159.665 39.5614 159.854 39.5791 160.03L40.0529 163.766V163.814C40.2424 165.185 40.6215 167.361 41.1427 169.962C41.664 172.563 42.3273 175.212 43.0855 177.718C43.9858 180.793 44.9335 183.299 45.5495 184.907C46.4971 187.319 47.587 189.684 48.819 192.002C49.0917 192.546 49.3645 192.995 49.6109 193.4L49.7666 193.657C49.814 193.752 49.8733 193.846 49.9325 193.941C49.9917 194.035 50.051 194.13 50.0983 194.224L51.1408 195.974L51.1882 196.069C53.2731 199.38 55.8792 202.312 58.9592 204.771C60.1911 205.765 61.5179 206.616 62.892 207.42C62.9631 207.514 63.0223 207.609 63.0815 207.703C63.1407 207.798 63.2 207.893 63.2711 207.987C64.2662 209.406 65.356 210.73 66.5406 211.913C67.7252 213.048 68.9572 214.136 70.284 215.082L70.3787 215.129C71.6581 216.028 73.0322 216.832 74.4538 217.541C79.1922 219.906 84.594 221.419 90.896 222.081C93.4548 222.365 96.0609 222.507 98.667 222.507H98.7618C101.273 222.507 103.832 222.318 106.343 222.034H106.391C108.76 221.75 111.176 221.325 113.498 220.757C114.195 220.611 114.834 220.436 115.417 220.277C115.588 220.23 115.754 220.185 115.915 220.142L116.768 219.906L117.052 219.811L117.858 219.575C118.616 219.338 119.374 219.102 120.227 218.818C120.843 218.581 121.459 218.345 122.122 218.109C122.501 218.44 122.833 218.723 123.259 219.054L123.307 219.102C125.723 220.994 128.377 222.507 131.22 223.595C131.789 223.831 132.452 224.068 133.494 224.399C133.755 224.493 134.016 224.576 134.276 224.659C134.537 224.742 134.797 224.824 135.058 224.919L135.295 225.014C135.773 225.163 136.271 225.293 136.787 225.429C137.088 225.508 137.397 225.589 137.712 225.676C138.205 225.817 138.673 225.905 139.173 226C139.345 226.032 139.52 226.065 139.702 226.101L140.507 226.243L140.697 226.291C141.076 226.338 141.455 226.385 141.834 226.48L143.066 226.669L145.483 226.905H145.625C145.828 226.905 146.017 226.919 146.193 226.932C146.345 226.943 146.488 226.953 146.62 226.953L148.326 227H149.747C150.221 227 150.884 227 151.642 226.953C153.68 226.811 155.67 226.574 157.66 226.149L159.271 225.818L159.413 225.77C159.84 225.676 160.219 225.581 160.598 225.439L160.977 225.345L162.02 225.061L163.82 224.493L164.436 224.304C164.616 224.233 164.795 224.168 164.977 224.102C165.275 223.994 165.581 223.883 165.905 223.737L167.137 223.216C167.99 222.885 168.795 222.46 169.601 222.034C170.217 221.703 170.833 221.372 171.402 221.041L171.591 220.946C172.728 220.237 173.818 219.433 174.861 218.581L175.145 218.345C175.287 218.203 175.441 218.073 175.595 217.943C175.749 217.813 175.903 217.683 176.045 217.541C177.751 218.203 179.457 218.771 181.163 219.244C186.091 220.71 191.208 221.608 196.326 221.939C202.012 222.318 207.745 221.703 213.242 220.142C216.274 219.244 219.165 217.919 221.818 216.217C224.709 214.372 227.22 212.007 229.21 209.264L229.258 209.217C230.253 207.798 231.106 206.332 231.864 204.771C233.238 201.744 234.043 198.528 234.328 195.265C234.47 193.988 234.517 192.758 234.47 191.481V190.488C234.423 189.827 234.375 189.307 234.328 188.787C234.328 188.686 234.314 188.583 234.301 188.489C234.291 188.407 234.28 188.331 234.28 188.265L234.138 186.941L233.854 185.617C233.83 185.522 233.818 185.439 233.806 185.357C233.795 185.274 233.783 185.191 233.759 185.097C233.664 184.624 233.522 184.009 233.333 183.347L232.764 181.502C232.622 180.982 232.432 180.509 232.195 180.036L231.437 178.239C231.248 177.813 231.106 177.529 230.963 177.246L230.537 176.489C230.443 176.319 230.356 176.15 230.27 175.983C230.142 175.732 230.016 175.487 229.874 175.259L228.736 173.415L228.642 173.273C227.741 171.901 226.794 170.672 225.846 169.442L227.125 167.597C229.115 164.381 230.632 160.929 231.674 157.287L231.864 156.578C232.859 152.889 233.617 149.152 234.091 145.369V145.274L234.186 144.47C234.28 143.855 234.375 143.193 234.422 142.484L234.659 139.788L234.707 138.984C234.802 137.234 234.896 135.437 234.849 133.45C234.802 129.052 234.422 124.653 233.712 120.302C233.238 117.512 232.574 114.721 231.769 111.978C232.622 111.174 233.427 110.323 234.186 109.424C236.602 106.492 238.592 103.276 240.061 99.8235C241.009 97.7425 242.43 94.3372 244.326 88.9456C246.221 83.5539 248.069 77.2637 249.68 70.8789C251.291 64.494 252.76 57.6835 253.803 51.346C254.798 45.5287 255.508 39.806 255.84 35.3129C255.982 32.9009 256.03 30.5361 255.982 28.1241Z",
        stroke: "white",
        "stroke-width": "12",
        mask: "url(#path-1-outside-1_604_2)"
      }), /* @__PURE__ */ jsx("path", {
        "fill-rule": "evenodd",
        "clip-rule": "evenodd",
        d: "M255.982 28.1241L255.935 27.2728C255.935 26.8944 255.887 26.2796 255.793 25.381C255.752 24.8902 255.675 24.3995 255.594 23.8782L255.556 23.631V23.5837C255.414 22.6378 255.177 21.6919 254.845 20.746L254.324 19.5164C254.087 19.0434 253.85 18.5705 253.566 18.1448C252.997 17.2462 252.286 16.4422 251.433 15.78C250.296 14.8341 248.922 14.172 247.453 13.8409C246.884 13.6991 246.316 13.6518 245.747 13.6045L245.084 13.5572H243.947C243.236 13.5572 242.525 13.6518 241.814 13.7464C241.104 13.8409 240.345 14.0301 239.635 14.2193L238.971 14.4085C238.118 14.6923 237.313 15.0233 236.555 15.4017C233.238 17.057 230.537 19.5637 228.547 21.5501C227.9 22.1953 227.254 22.8846 226.622 23.5579C226.329 23.8712 226.037 24.1821 225.751 24.4823C225.056 25.2391 224.319 25.9959 223.582 26.7527C223.213 27.131 222.845 27.5093 222.482 27.8876C220.586 29.7794 218.549 31.482 216.369 32.9955C214.284 34.4143 212.057 35.5494 209.688 36.4007L205.092 38.1506L204.76 38.2925C204.239 38.529 203.718 38.7655 203.244 39.0019L202.486 39.3803L201.964 39.6168C201.348 39.9006 200.732 40.2316 200.164 40.5627C197.652 41.9342 195.236 43.495 192.914 45.1976L192.867 45.2449L192.061 45.8597C191.492 46.2854 190.924 46.711 190.403 47.184L188.081 49.1704L186.47 50.6838C183.721 53.2378 181.352 56.1228 179.41 59.2915C179.291 59.4807 179.173 59.6817 179.054 59.8827C178.936 60.0837 178.817 60.2848 178.699 60.4739L178.13 60.2374C172.823 58.2983 167.421 56.7376 161.925 55.5079C150.695 53.0486 139.18 52.1027 127.666 52.8121C126.766 52.8594 125.913 52.9067 125.06 53.0013C124.681 53.0486 124.302 53.0959 123.923 53.0959L122.501 53.2378L121.98 53.2851L120.322 53.4743C119.563 53.5688 118.805 53.6634 118.142 53.758L117.052 53.8999C114.92 54.231 113.451 54.4674 112.408 54.7039C109.092 55.3188 105.822 56.312 102.695 57.6362C101.605 55.2242 100.231 52.954 98.5723 50.873C97.4824 49.4542 96.2978 48.1299 95.0185 46.8529C94.1656 46.0016 93.2652 45.1503 92.2228 44.2517L91.5594 43.7315C91.3916 43.6059 91.2332 43.4803 91.0798 43.3588C90.8868 43.2058 90.7018 43.0592 90.517 42.9274L90.1379 42.6437L89.9484 42.5005C89.6045 42.2399 89.1938 41.9285 88.7164 41.6505L88.4321 41.4613C87.9582 41.1302 87.437 40.7992 86.821 40.4208L86.7736 40.3735C86.6224 40.2854 86.4644 40.1907 86.2997 40.0919C85.8454 39.8193 85.34 39.5161 84.7835 39.2384L83.8358 38.7655C83.5515 38.6236 83.2672 38.4817 82.9829 38.3871L81.7035 37.8196L79.3817 36.921L76.0648 35.8332L75.2119 35.5494C74.2642 35.2656 73.4113 34.9819 72.6532 34.6981H72.6058L71.8476 34.4143L70.8526 34.036L69.1467 33.2319C67.0144 32.286 64.9769 31.151 63.0342 29.7794L62.9868 29.7321C60.9019 28.2187 58.9592 26.6106 57.0638 24.8607L55.2632 23.2527C54.8523 22.881 54.4378 22.5023 54.0199 22.1204C52.896 21.0935 51.7464 20.0431 50.5722 19.0434C48.1082 16.9151 45.7864 15.1652 43.6067 13.6518C41.2849 11.9491 38.8209 10.4357 36.2622 9.15873C34.9354 8.4966 33.6087 7.88177 32.2345 7.40882L32.0924 7.36152C30.6235 6.84127 29.1072 6.46291 27.5435 6.22644C25.8377 5.94267 24.1318 5.94267 22.426 6.13185C20.6728 6.32103 18.967 6.84127 17.4033 7.5507L17.3085 7.598C15.9344 8.26013 14.655 9.15874 13.4704 10.1992L13.3757 10.2938C12.9492 10.7195 12.5227 11.1451 12.0963 11.6181L11.812 11.9964C11.5277 12.3275 11.2908 12.6586 11.0538 12.9896C10.2483 14.1247 9.53755 15.3544 8.96894 16.6314L8.54248 17.5773C8.4951 17.6955 8.45956 17.8019 8.42994 17.8906C8.40033 17.9793 8.37664 18.0502 8.35294 18.0975C8.32366 18.156 8.25818 18.3409 8.16769 18.5964C8.11176 18.7544 8.04627 18.9393 7.97387 19.138L7.92649 19.2799C7.54742 20.3677 7.26311 21.5028 7.02619 22.6378C6.6945 24.2932 6.4102 25.9958 6.22066 27.6984L6.17328 28.1714C6.14885 28.3421 6.13701 28.5253 6.12478 28.7147C6.1133 28.8926 6.10146 29.0759 6.07851 29.2592L6.03112 30.7726C5.98374 31.9077 5.98374 32.9955 6.07851 34.1306L6.12589 34.7927C6.4102 37.6304 7.02619 40.4208 7.92649 43.1639C8.70904 45.4153 9.67046 47.622 10.5935 49.7407L10.6748 49.9271L10.9591 50.6365C12.0015 52.954 12.8544 55.2242 13.66 57.4943L13.9443 58.2983C14.0455 58.6352 14.1528 58.96 14.2575 59.2771C14.4468 59.8505 14.6278 60.3987 14.7498 60.9469V61.0415L14.9867 61.7982C15.0341 61.9637 15.0815 62.1411 15.1289 62.3184C15.1763 62.4958 15.2236 62.6731 15.271 62.8387L15.7449 64.8251L15.7922 64.967C15.9818 65.7237 16.1713 66.6223 16.3135 67.5682L16.503 68.7033L16.6925 69.6492C16.6925 69.7201 16.7044 69.7911 16.7162 69.862C16.7281 69.9329 16.7399 70.0039 16.7399 70.0748L17.4033 74.757V74.8989C17.427 74.9935 17.4388 75.0999 17.4507 75.2064C17.4625 75.3128 17.4744 75.4192 17.4981 75.5138C17.5241 75.6698 17.5502 75.833 17.5772 76.0023C17.6485 76.449 17.7267 76.9385 17.8298 77.4529L17.9719 78.115C18.0667 78.6825 18.2088 79.2974 18.3984 79.9595C18.4458 80.196 18.4931 80.4325 18.5879 80.6216C18.73 81.1891 18.8722 81.7093 19.0143 82.2295C19.962 85.3982 21.194 88.4726 22.7103 91.4049C23.3722 92.7262 24.0341 93.8672 24.6644 94.9539L24.9374 95.425C25.1283 95.7517 25.3349 96.0784 25.5301 96.387C25.674 96.6146 25.8118 96.8323 25.9324 97.033L27.3066 99.114C28.6807 101.148 30.197 103.087 31.8081 104.931C33.0401 106.397 34.0825 107.533 35.0776 108.526L35.125 108.573C37.2099 110.749 39.5317 112.688 41.9957 114.438L41.7959 115.032C41.5325 115.813 41.2751 116.577 41.048 117.37C40.1003 120.775 39.4843 124.275 39.2474 127.775L39.2 128.106L39.1508 128.75C39.0479 130.083 38.887 132.166 38.7262 135.579C38.5366 139.599 38.5366 145.983 38.8209 151.281C38.9631 153.74 39.1526 156.247 39.3895 158.327C39.4193 158.743 39.4677 159.121 39.5113 159.462C39.5372 159.665 39.5614 159.854 39.5791 160.03L40.0529 163.766V163.814C40.2424 165.185 40.6215 167.361 41.1427 169.962C41.664 172.563 42.3273 175.212 43.0855 177.718C43.9858 180.793 44.9335 183.299 45.5495 184.907C46.4971 187.319 47.587 189.684 48.819 192.002C49.0917 192.546 49.3645 192.995 49.6109 193.4L49.7666 193.657C49.814 193.752 49.8733 193.846 49.9325 193.941C49.9917 194.035 50.051 194.13 50.0983 194.224L51.1408 195.974L51.1882 196.069C53.2731 199.38 55.8792 202.312 58.9592 204.771C60.1911 205.765 61.5179 206.616 62.892 207.42C62.9631 207.514 63.0223 207.609 63.0815 207.703C63.1407 207.798 63.2 207.893 63.2711 207.987C64.2662 209.406 65.356 210.73 66.5406 211.913C67.7252 213.048 68.9572 214.136 70.284 215.082L70.3787 215.129C71.6581 216.028 73.0322 216.832 74.4538 217.541C79.1922 219.906 84.594 221.419 90.896 222.081C93.4548 222.365 96.0609 222.507 98.667 222.507H98.7618C101.273 222.507 103.832 222.318 106.343 222.034H106.391C108.76 221.75 111.176 221.325 113.498 220.757C114.195 220.611 114.834 220.436 115.417 220.277C115.588 220.23 115.754 220.185 115.915 220.142L116.768 219.906L117.052 219.811L117.858 219.575C118.616 219.338 119.374 219.102 120.227 218.818C120.843 218.581 121.459 218.345 122.122 218.109C122.501 218.44 122.833 218.723 123.259 219.054L123.307 219.102C125.723 220.994 128.377 222.507 131.22 223.595C131.789 223.831 132.452 224.068 133.494 224.399C133.755 224.493 134.016 224.576 134.276 224.659C134.537 224.742 134.797 224.824 135.058 224.919L135.295 225.014C135.773 225.163 136.271 225.293 136.787 225.429C137.088 225.508 137.397 225.589 137.712 225.676C138.205 225.817 138.673 225.905 139.173 226C139.345 226.032 139.52 226.065 139.702 226.101L140.507 226.243L140.697 226.291C141.076 226.338 141.455 226.385 141.834 226.48L143.066 226.669L145.483 226.905H145.625C145.828 226.905 146.017 226.919 146.193 226.932C146.345 226.943 146.488 226.953 146.62 226.953L148.326 227H149.747C150.221 227 150.884 227 151.642 226.953C153.68 226.811 155.67 226.574 157.66 226.149L159.271 225.818L159.413 225.77C159.84 225.676 160.219 225.581 160.598 225.439L160.977 225.345L162.02 225.061L163.82 224.493L164.436 224.304C164.616 224.233 164.795 224.168 164.977 224.102C165.275 223.994 165.581 223.883 165.905 223.737L167.137 223.216C167.99 222.885 168.795 222.46 169.601 222.034C170.217 221.703 170.833 221.372 171.402 221.041L171.591 220.946C172.728 220.237 173.818 219.433 174.861 218.581L175.145 218.345C175.287 218.203 175.441 218.073 175.595 217.943C175.749 217.813 175.903 217.683 176.045 217.541C177.751 218.203 179.457 218.771 181.163 219.244C186.091 220.71 191.208 221.608 196.326 221.939C202.012 222.318 207.745 221.703 213.242 220.142C216.274 219.244 219.165 217.919 221.818 216.217C224.709 214.372 227.22 212.007 229.21 209.264L229.258 209.217C230.253 207.798 231.106 206.332 231.864 204.771C233.238 201.744 234.043 198.528 234.328 195.265C234.47 193.988 234.517 192.758 234.47 191.481V190.488C234.423 189.827 234.375 189.307 234.328 188.787C234.328 188.686 234.314 188.583 234.301 188.489C234.291 188.407 234.28 188.331 234.28 188.265L234.138 186.941L233.854 185.617C233.83 185.522 233.818 185.439 233.806 185.357C233.795 185.274 233.783 185.191 233.759 185.097C233.664 184.624 233.522 184.009 233.333 183.347L232.764 181.502C232.622 180.982 232.432 180.509 232.195 180.036L231.437 178.239C231.248 177.813 231.106 177.529 230.963 177.246L230.537 176.489C230.443 176.319 230.356 176.15 230.27 175.983C230.142 175.732 230.016 175.487 229.874 175.259L228.736 173.415L228.642 173.273C227.741 171.901 226.794 170.672 225.846 169.442L227.125 167.597C229.115 164.381 230.632 160.929 231.674 157.287L231.864 156.578C232.859 152.889 233.617 149.152 234.091 145.369V145.274L234.186 144.47C234.28 143.855 234.375 143.193 234.422 142.484L234.659 139.788L234.707 138.984C234.802 137.234 234.896 135.437 234.849 133.45C234.802 129.052 234.422 124.653 233.712 120.302C233.238 117.512 232.574 114.721 231.769 111.978C232.622 111.174 233.427 110.323 234.186 109.424C236.602 106.492 238.592 103.276 240.061 99.8235C241.009 97.7425 242.43 94.3372 244.326 88.9456C246.221 83.5539 248.069 77.2637 249.68 70.8789C251.291 64.494 252.76 57.6835 253.803 51.346C254.798 45.5287 255.508 39.806 255.84 35.3129C255.982 32.9009 256.03 30.5361 255.982 28.1241Z",
        stroke: "white",
        "stroke-width": "5"
      }), /* @__PURE__ */ jsx("path", {
        d: "M54.7415 114.404C54.7415 114.404 54.7888 114.357 54.8833 114.215L54.6471 114.357L54.7415 114.404Z",
        fill: "white"
      }), /* @__PURE__ */ jsx("path", {
        d: "M154.106 196.568C153.111 195.526 152.258 194.531 151.5 193.583C151.358 193.394 151.216 193.251 151.073 193.109C150.931 193.015 150.836 192.872 150.694 192.778C150.457 192.588 150.173 192.493 149.841 192.399C149.32 192.256 148.799 192.304 148.325 192.446C147.946 192.588 147.614 192.778 147.33 193.015C147.188 193.109 147.141 193.204 147.046 193.346L146.714 193.725L146.43 194.057L145.34 195.289C144.629 196.094 143.539 197.232 142.118 198.653C138.09 202.586 133.589 206.045 128.756 208.888C127.476 209.646 126.102 210.357 124.681 211.068C126.007 211.636 127.239 212.063 128.471 212.584C130.414 213.342 132.357 214.148 134.915 215.143C135.342 215.332 135.911 215.522 136.763 215.806C137.19 215.948 137.664 216.09 138.232 216.28C138.801 216.47 139.464 216.612 140.222 216.801C140.791 216.943 141.644 217.086 142.497 217.275C142.923 217.37 143.397 217.417 143.824 217.465L144.487 217.559L145.15 217.607L146.382 217.702C146.761 217.749 147.093 217.749 147.377 217.749L148.325 217.796H149.131C149.604 217.796 150.315 217.796 151.073 217.749C152.684 217.654 154.248 217.417 155.812 217.133L157.233 216.849C157.707 216.754 158.134 216.612 158.513 216.517L159.65 216.185L160.645 215.854C161.261 215.617 161.83 215.474 162.303 215.285L163.441 214.811C164.057 214.574 164.673 214.337 165.241 214.053C165.81 213.769 166.331 213.579 166.852 213.342C167.895 212.868 168.842 212.442 169.79 212.063C170.738 211.684 171.685 211.257 172.68 210.831L173.486 210.452C169.127 208.414 165.004 205.95 161.166 203.06C158.702 201.07 156.286 198.938 154.106 196.568Z",
        fill: "white"
      }), /* @__PURE__ */ jsx("path", {
        d: "M102.363 149.421C109.281 149.421 114.872 143.83 114.872 136.912C114.872 129.994 109.281 124.403 102.363 124.403C95.4446 124.403 89.8533 129.994 89.8533 136.912C89.8533 143.83 95.4446 149.421 102.363 149.421Z",
        fill: "white"
      }), /* @__PURE__ */ jsx("path", {
        d: "M190.876 147.62C196.799 147.62 201.632 142.835 201.632 136.912C201.632 130.989 196.846 126.156 190.923 126.156C185 126.156 180.167 130.941 180.167 136.864C180.167 142.787 184.953 147.573 190.876 147.62Z",
        fill: "white"
      }), /* @__PURE__ */ jsx("path", {
        d: "M70.3311 89.7173C70.6628 89.1961 70.9945 88.6749 71.3735 88.1536C71.7526 87.6324 72.1317 87.1112 72.5107 86.59C72.7003 86.353 72.9372 86.0687 73.1267 85.8318L73.7901 85.0737C74.2166 84.5524 74.6904 84.0786 75.1642 83.6048C76.1593 82.6097 77.2018 81.7094 78.2916 80.9039C79.4288 80.0984 80.6134 79.3876 81.8454 78.7242C82.4614 78.3925 83.03 78.1082 83.646 77.8239L83.8829 77.7292H83.9303L83.5512 76.971C83.4091 76.6867 83.2669 76.4024 83.0774 76.1181C82.4614 74.9809 81.798 73.9384 81.1346 72.8486C78.4811 68.7262 75.5433 64.7933 72.3212 61.0974C69.2886 57.591 66.3508 54.511 63.7921 51.9523C61.2334 49.3936 59.0063 47.4034 57.4427 46.0293C55.879 44.6552 54.9787 43.897 54.9787 43.897C54.9787 43.897 54.0784 43.1389 52.5147 41.8121C50.9511 40.4854 48.5345 38.6374 45.5967 36.5051C42.2798 34.0412 38.8208 31.7194 35.2196 29.5871C33.1821 28.3551 31.0972 27.2653 28.9649 26.2702C27.8751 25.7964 26.7853 25.3225 25.648 24.9908C25.1268 24.8013 24.5582 24.7065 23.9896 24.6118C23.5158 24.517 23.0419 24.4696 22.5681 24.517C22.4733 24.517 22.4259 24.517 22.3312 24.5644C22.2838 24.5644 22.2364 24.6118 22.189 24.6118C22.1416 24.6118 22.1416 24.6592 22.0942 24.6592C22.0942 24.6592 22.0942 24.6118 22.0469 24.7065C21.9047 24.8961 21.7626 25.0856 21.6678 25.2751L21.4783 25.5594L21.4309 25.8438C21.0518 26.8862 20.8623 27.976 20.8149 29.0659C20.7675 31.5772 20.957 34.0412 21.3835 36.5051C21.7626 39.0165 22.2364 41.4805 22.7102 43.897C23.1841 46.3136 23.6579 48.6354 24.0844 50.8625C24.7951 54.5584 25.3637 57.591 25.6007 59.1547C25.6954 59.7233 25.7428 60.2445 25.8376 60.7657L26.2166 62.5189C26.5957 63.9404 26.8326 65.4093 27.1169 66.8782L27.3065 67.9681C27.3539 68.3471 27.4012 68.7262 27.4486 69.0579L27.7803 71.2849L28.112 73.4172C28.2068 74.0806 28.3015 74.7914 28.4437 75.4073C28.5858 76.0233 28.6806 76.7341 28.8701 77.3975C29.0597 78.0609 29.2018 78.7242 29.3914 79.3402C30.1495 81.8989 31.1446 84.3629 32.3766 86.7795C32.9925 87.9641 33.6085 89.1013 34.2719 90.1438C34.6036 90.7124 34.9353 91.2336 35.267 91.7548L35.7882 92.5129L36.262 93.1763C37.4466 94.8821 38.726 96.5406 40.1001 98.1516C41.2374 99.5258 42.2324 100.568 42.8958 101.279C45.3598 103.885 47.3025 105.923 49.1031 107.913L51.804 110.993C52.6569 111.988 53.5572 113.03 54.5522 114.073L54.7418 114.215C55.8316 112.035 56.7319 110.235 57.7743 108.434C58.9589 106.396 60.2857 104.406 61.7546 102.511C62.2284 101.895 62.8918 100.995 63.6973 99.8101L65.0241 97.9147L65.4032 97.3935L65.8296 96.7301C66.1139 96.3037 66.4456 95.8772 66.7299 95.4034C67.2985 94.5031 67.9145 93.5554 68.4831 92.6077C68.7674 92.1339 69.0991 91.6127 69.4308 91.0914C69.7625 90.5702 69.9994 90.2385 70.3311 89.7173Z",
        fill: "white"
      }), /* @__PURE__ */ jsx("path", {
        d: "M245.225 27.8815C245.225 27.7393 245.225 27.5498 245.178 27.4077C245.036 27.2655 244.799 27.1707 244.562 27.1234C244.277 27.1234 243.993 27.2181 243.756 27.3129C242.809 27.7393 241.861 28.2606 241.055 28.9239C238.923 30.5824 236.98 32.4304 235.227 34.5152C233.047 36.9318 230.157 40.533 227.883 43.613C225.608 46.6929 223.855 49.1095 223.855 49.1095C223.855 49.1095 221.817 51.9999 219.353 55.6011C216.89 59.2023 214.141 63.4668 212.53 66.0256L209.45 70.8587C207.46 74.0808 205.138 77.1134 202.485 79.8143L202.58 79.9091L203.669 80.762C204.428 81.4253 205.328 82.0887 206.276 82.9416L209.308 85.7373C210.351 86.8271 211.44 87.9643 212.578 89.2437L214.236 91.2338L215.089 92.2763C215.373 92.6553 215.61 93.0344 215.894 93.3661L217.506 95.6405C218.027 96.4461 218.548 97.299 219.069 98.1045C221.107 101.469 222.86 105.023 224.234 108.718C224.471 108.292 224.66 107.913 224.897 107.487C225.513 106.255 226.035 105.07 226.556 103.885C227.598 101.421 228.688 98.8626 230.157 95.5931C230.868 93.9821 232.242 90.8074 234.043 85.5477C235.748 80.6198 237.549 74.6021 239.113 68.3474C240.676 62.0927 242.05 55.5537 243.093 49.5833C244.088 43.613 244.751 38.3533 245.036 34.5626C245.178 32.6673 245.225 31.151 245.225 30.1085C245.225 29.0661 245.225 28.5449 245.225 28.5449V27.8815Z",
        fill: "white"
      }), /* @__PURE__ */ jsx("path", {
        d: "M214.284 171.502C213.905 171.123 213.478 170.791 213.099 170.46C212.72 170.128 212.294 169.749 211.914 169.465C211.109 168.801 210.303 168.185 209.451 167.569C208.598 166.953 207.792 166.385 206.987 165.816C206.181 165.247 205.328 164.726 204.523 164.205L203.291 163.447L202.675 163.068L202.296 162.878C201.585 162.499 200.921 162.073 200.305 161.741C199.073 161.078 198.078 160.556 197.368 160.225C195.141 159.088 193.34 158.14 191.682 157.192C191.302 156.955 190.923 156.766 190.544 156.624C177.324 150.558 169.222 148.142 167.184 146.862C158.655 111.182 164.72 77.0186 166.663 67.8735C164.388 67.2101 162.067 66.6415 159.697 66.0729C154.438 64.8883 149.083 64.1302 143.682 63.7037C140.649 63.4668 137.664 63.372 134.773 63.372C136.242 74.602 141.549 121.986 128.471 146.815C124.633 148.995 120.653 150.89 116.531 152.501C114.351 153.638 105.538 157.24 99.3302 159.94C97.4823 160.888 95.5395 161.836 93.0282 163.02C90.5642 164.205 88.2424 165.532 85.968 167.001L85.8258 167.095L85.4941 167.332L84.8308 167.759C84.4043 168.043 83.9778 168.375 83.5514 168.706C82.6985 169.322 81.8456 169.986 81.04 170.697C79.3816 172.118 77.8179 173.634 76.349 175.293C73.3165 178.657 71.042 182.59 69.6205 186.855C68.9571 188.987 68.5781 191.214 68.5781 193.488C68.5781 195.715 69.0045 197.895 69.81 199.932C70.2365 200.928 70.7577 201.923 71.3737 202.823C71.9897 203.723 72.7005 204.576 73.506 205.382C74.3115 206.187 75.1644 206.898 76.0647 207.514C77.0124 208.177 77.9601 208.746 78.9551 209.267C83.0302 211.305 87.579 212.347 92.0805 212.821C96.4872 213.342 100.894 213.342 105.301 212.821C107.386 212.584 109.423 212.205 111.461 211.731C112.456 211.542 113.403 211.21 114.351 210.973C115.299 210.736 116.199 210.404 117.147 210.073C120.558 208.888 123.828 207.372 126.908 205.571C131.504 202.87 135.768 199.648 139.559 195.905C140.933 194.578 141.928 193.488 142.639 192.73L143.634 191.546C143.634 191.546 143.729 191.451 143.871 191.261L144.203 190.882C144.392 190.693 144.582 190.456 144.866 190.219C145.909 189.271 147.188 188.703 148.562 188.56C148.989 187.234 149.226 185.859 149.32 184.438C149.415 183.443 149.415 182.4 149.368 181.405C149.368 180.884 149.32 180.316 149.273 179.747C149.273 179.605 149.273 179.463 149.226 179.32L149.178 178.847C149.131 178.515 149.083 178.183 149.036 177.804L148.989 177.567C147.899 177.378 146.856 177.046 145.861 176.62C143.871 176.477 141.976 175.861 140.27 174.866C139.796 174.582 139.322 174.203 138.801 173.871C138.327 173.445 137.853 173.018 137.427 172.592C136.479 171.55 135.626 170.412 134.963 169.133C134.773 168.801 134.537 168.375 134.347 167.854C134.205 167.617 134.11 167.332 133.968 167.001C133.921 166.859 133.826 166.716 133.778 166.527L133.541 165.863C133.447 165.532 133.352 165.2 133.257 164.821C133.21 164.631 133.162 164.442 133.115 164.3L133.068 164.015L133.02 163.873C133.02 163.826 133.068 163.826 133.115 163.779C133.399 163.494 133.636 163.21 133.968 162.926L134.821 162.12C135.152 161.788 135.579 161.457 135.958 161.125L136.574 160.604L137.285 160.13C139.322 158.708 141.549 157.666 143.919 157.003C146.43 156.339 149.083 156.15 151.689 156.434C153.727 156.671 155.717 157.097 157.66 157.761C158.371 157.998 158.987 158.235 159.366 158.377C159.745 158.519 159.982 158.614 159.982 158.614L160.313 158.756C160.55 158.851 160.929 159.04 161.451 159.277C161.972 159.514 162.683 159.893 163.583 160.367C164.009 160.604 164.531 160.888 165.052 161.267C165.336 161.457 165.62 161.599 165.905 161.788L166.142 161.931L166.521 162.167L166.9 162.452L167.326 162.783C167.516 162.926 167.8 163.115 168.037 163.352L168.274 163.542L168.369 163.636V163.779L168.226 164.395C168.132 164.821 167.99 165.342 167.8 165.863L167.658 166.243L167.563 166.479C167.516 166.622 167.468 166.764 167.374 166.953C166.758 168.47 166.047 169.891 165.147 171.218C164.151 172.734 162.919 174.108 161.545 175.293C160.313 176.335 158.939 177.236 157.518 177.899C156.238 178.468 154.959 178.941 153.585 179.226L152.921 179.368H152.874V179.415C152.874 180.079 152.874 180.742 152.779 181.405C152.637 182.59 152.353 183.775 151.926 184.912C151.453 186.191 150.742 187.376 149.842 188.418C150.126 188.466 150.458 188.513 150.742 188.56C151.453 188.75 152.116 189.034 152.732 189.461C153.064 189.698 153.348 189.934 153.632 190.171C153.917 190.456 154.201 190.787 154.343 190.977C155.054 191.877 155.859 192.825 156.807 193.773C158.844 195.952 161.119 197.99 163.488 199.79C169.601 204.434 176.566 207.94 183.911 210.073C188.128 211.352 192.487 212.11 196.894 212.394C201.443 212.726 206.039 212.252 210.446 210.973C212.625 210.31 214.71 209.362 216.605 208.177C219.449 206.377 221.676 203.818 223.097 200.785C223.571 199.79 223.903 198.701 224.187 197.658C224.471 196.568 224.613 195.478 224.708 194.341C224.803 193.204 224.85 192.114 224.803 190.977C224.803 190.408 224.708 189.887 224.613 189.318L224.519 188.466L224.329 187.66C224.187 187.139 224.14 186.57 223.95 186.049C223.76 185.528 223.618 185.007 223.429 184.485C223.334 184.201 223.287 183.964 223.144 183.68L222.813 182.922L222.481 182.164C222.386 181.927 222.244 181.69 222.102 181.453C221.865 180.979 221.581 180.458 221.344 179.984L220.491 178.61C219.306 176.809 217.932 175.103 216.416 173.54C215.847 172.971 215.042 172.26 214.284 171.502ZM160.835 144.683C160.124 144.683 159.413 144.493 158.75 144.209C156.949 143.451 155.054 142.835 153.111 142.456C152.069 142.219 151.026 142.077 149.984 141.982C149.557 141.935 149.226 141.935 148.989 141.935H147.235C146.193 141.982 145.151 142.124 144.108 142.314C142.971 142.551 141.881 142.835 140.791 143.214C140.317 143.356 139.844 143.593 139.464 143.735C139.085 143.877 138.801 144.019 138.612 144.114C137.19 144.778 136.1 144.683 134.252 144.493C134.773 142.74 135.389 141.603 137 140.75C137.237 140.655 137.569 140.466 137.996 140.276C138.422 140.087 138.943 139.85 139.512 139.66C140.791 139.186 142.071 138.855 143.397 138.618C144.582 138.381 145.814 138.286 147.046 138.191C147.52 138.191 147.946 138.191 148.23 138.191H149.083C149.462 138.191 149.842 138.191 150.221 138.239C151.453 138.333 152.637 138.476 153.822 138.76C156.001 139.234 158.134 139.897 160.171 140.845C161.83 141.603 162.493 142.693 163.062 144.446C162.398 144.588 161.593 144.683 160.835 144.683Z",
        fill: "white"
      })]
    });
  };
  const Operator = window["__foo__"].Operator;
  const OperatorConfig = window["__foo__"].OperatorConfig;
  const registerOperator = window["__foo__"].registerOperator;
  const useOperatorExecutor = window["__foo__"].useOperatorExecutor;
  const types = window["__foo__"].types;

  class OpenDagsHubPanel extends Operator {
    get config() {
      return new OperatorConfig({
        name: "open_dagshub_panel",
        label: "Open DagsHub Panel"
      });
    }

    useHooks() {
      const openPanelOperator = useOperatorExecutor("open_panel");
      return {openPanelOperator};
    }

    async resolvePlacement() {
      return new types.Placement(
        types.Places.SAMPLES_GRID_SECONDARY_ACTIONS,
        new types.Button({
          label: "Open DagsHub Panel",
          icon: "/assets/dagshub.svg"
        })
      );
    }

    async execute({hooks}) {
      const {openPanelOperator} = hooks;
      openPanelOperator.execute({
        name: "dagshub",
        isActive: true,
        layout: "horizontal"
      });
    }
  }

  registerOperator(OpenDagsHubPanel, "dagshub");
  registerComponent({
    name: "dagshub",
    label: "DagsHub",
    component: Plugin,
    type: PluginComponentType.Panel,
    Icon: DagsHubIcon,
    activator
  });

  function activator({dataset}) {
    return true;
  }
});
