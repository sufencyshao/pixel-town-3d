/**
 * LLM 接入层：统一封装各家模型 API
 * - openai 兼容协议：OpenAI / DeepSeek / Kimi / 智谱 / 通义 / Gemini(OpenAI兼容端点) / Ollama 等一切兼容端点
 * - anthropic 协议：Claude 系列
 * - demo：内置演示模式，无需 API Key 即可体验完整功能
 * v2：错误信息可读化；400/422 参数自动兼容回退（stream_options → max_completion_tokens → temperature）；
 *     fetchModels 获取服务商模型列表
 */

/** v3.7 系统代理检测（macOS：scutil --proxy），供中转站等被墙域名使用 */
let _sysProxyCache = { time: 0, proxy: null };
function systemProxy() {
  if (_sysProxyCache.time > Date.now() - 5 * 60e3) return _sysProxyCache.proxy; // 缓存 5 分钟
  try {
    const { execSync } = require('child_process');
    const out = execSync('scutil --proxy', { timeout: 3000 }).toString();
    // 分别独立捕获 host 与 port（scutil 输出顺序可能 Port 在 Proxy 之前）
    const host = (out.match(/HTTPSProxy\s*:\s*([^\s]+)/) || [])[1];
    const port = (out.match(/HTTPSPort\s*:\s*(\d+)/) || [])[1];
    const enabled = /HTTPSEnable\s*:\s*1/.test(out);
    const proxy = enabled && host && port ? `http://${host.trim()}:${port}` : null;
    _sysProxyCache = { time: Date.now(), proxy };
    return proxy;
  } catch (e) { return null; }
}

/** v3.7 代理感知 fetch：有系统代理时用 undici fetch + ProxyAgent（原生 fetch 的 dispatcher 在新 undici 下不兼容） */
function proxyAwareFetch(url, opts = {}) {
  const proxyUrl = systemProxy();
  if (proxyUrl) {
    const { fetch: ufetch, ProxyAgent } = require('undici');
    return ufetch(url, Object.assign({}, opts, { dispatcher: new ProxyAgent(proxyUrl) }));
  }
  return fetch(url, opts);
}

/** v3.7 baseUrl 归一化：用户误把完整接口地址当 baseUrl 时自动剥掉尾部 */
function normalizeBaseUrl(base) {
  let b = String(base || '').trim().replace(/\/+$/, '');
  b = b.replace(/\/chat\/completions$/i, ''); // https://x.com/v1/chat/completions → https://x.com/v1
  return b;
}

function anthropicUrl(provider, endpoint) {
  let base = normalizeBaseUrl(provider.baseUrl || 'https://api.anthropic.com');
  base = base.replace(/\/(?:messages|models)$/i, '');
  return base + (/\/v1$/i.test(base) ? '/' : '/v1/') + endpoint;
}

function hideKey(error, provider) {
  if (!provider?.apiKey) return error;
  const message = String(error?.message || error).replaceAll(provider.apiKey, '[已隐藏]');
  const redacted = new Error(message);
  redacted.name = error?.name || 'Error';
  return redacted;
}

function pause(ms, signal) {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) { reject(signal.reason || new DOMException('已取消', 'AbortError')); return; }
    const onAbort = () => { clearTimeout(timer); signal.removeEventListener('abort', onAbort); reject(signal.reason || new DOMException('已取消', 'AbortError')); };
    const timer = setTimeout(() => { signal?.removeEventListener('abort', onAbort); resolve(); }, ms);
    signal?.addEventListener('abort', onAbort, { once: true });
  });
}

// 兼容分块 UTF-8、CRLF，以及末行没有换行符的流。
async function readSSE(body, onData) {
  if (!body) throw new Error('API 未返回响应内容');
  const reader = body.getReader(), decoder = new TextDecoder();
  let buffer = '';
  const line = text => {
    const trimmed = text.trim();
    if (!trimmed.startsWith('data:')) return;
    const data = trimmed.slice(5).trim();
    if (data === '[DONE]') return;
    let parsed;
    try { parsed = JSON.parse(data); } catch { return; }
    onData(parsed);
  };
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let idx;
      while ((idx = buffer.indexOf('\n')) >= 0) { line(buffer.slice(0, idx)); buffer = buffer.slice(idx + 1); }
    }
    buffer += decoder.decode();
    if (buffer.trim()) line(buffer);
  } finally { reader.releaseLock(); }
}

const DEMO_REPLIES = [
  '（演示模式）嗯嗯，我在听呢～你说的这个，后来怎么样了？',
  '（演示模式）哈哈，这个话题有意思！你先说说你的想法，我们再一起聊聊？',
  '（演示模式）我懂你的意思，换我的话可能会先缓一缓，再想下一步怎么办。',
  '（演示模式）辛苦啦～记得多喝点水，别把自己逼太紧。',
  '（演示模式）听起来不错呀！你是怎么想到的？',
];

const DEMO_PROACTIVE = [
  '（演示模式）在忙吗？刚刚突然想起你，想找你聊两句～',
  '（演示模式）跟你说，我今天碰到一件特别有意思的事，改天细聊！',
  '（演示模式）好久没聊了，最近过得怎么样呀？',
  '（演示模式）刚看到一句话想分享给你：「慢慢来，比较快。」',
];

const DEMO_MOMENTS = [
  '（演示模式）今天天气真好，出去走了走，心情都亮了☀️',
  '（演示模式）深夜码字，一杯咖啡一条命☕️，但热爱可抵岁月漫长。',
  '（演示模式）把房间收拾了一遍，断舍离真的让人神清气爽！',
  '（演示模式）读到一段很喜欢的话：把日子过成自己喜欢的样子。共勉～',
  '（演示模式）周末就要去爬山了，有没有同款爬山搭子？🏔️',
];

function rand(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function estimateTokens(text) {
  if (!text) return 0;
  // 粗略估算：中文约 1 字 = 1~2 token，这里取 1.5 字/token 的保守值
  let zh = 0, other = 0;
  for (const ch of text) /[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]/.test(ch) ? zh++ : other++;
  return Math.ceil(zh * 1.5 + other / 4);
}

/** 演示模式：模拟流式回复 */
async function demoStream(text, onDelta, signal) {
  const parts = text.match(/.{1,3}/gu) || [text];
  for (const p of parts) {
    await pause(30, signal);
    onDelta(p);
  }
  return text;
}

/* ---------------- 错误信息可读化（v2） ---------------- */

/**
 * 从 HTTP 错误响应体中提取可读信息。
 * 优先级：error.message → error.msg → message → error(字符串) → error.metadata 原文。
 * 输出格式：`HTTP {status}（{providerName}）：{信息 ≤200字}`；解析不出则用原文截断。
 */
function extractApiError(status, bodyText, providerName) {
  let raw = '';
  const text = String(bodyText || '');
  try {
    const j = JSON.parse(text);
    const err = j && j.error;
    if (typeof err === 'string') raw = err;
    else if (err && typeof err === 'object') raw = err.message || err.msg || '';
    if (!raw && j && typeof j.message === 'string') raw = j.message;
    if (!raw && err && typeof err === 'object') {
      // 部分服务商会把原始错误放在 metadata 里
      const meta = err.metadata || {};
      raw = meta.raw || meta.raw_error || meta.other || '';
      if (typeof raw !== 'string') raw = JSON.stringify(raw);
    }
  } catch {
    raw = text.trim();
  }
  raw = String(raw || '').trim();
  if (!raw) raw = '（服务商未返回错误详情）';
  if (raw.length > 200) raw = raw.slice(0, 200) + '…';
  return `HTTP ${status}（${providerName || '未知服务商'}）：${raw}`;
}

/** 网络/连接类错误可读化（AbortError 原样抛出，由调用方判断取消） */
function readableNetworkError(e, target) {
  if (e && e.name === 'AbortError') return e;
  const reason = (e && (e.cause?.message || e.message)) || '未知原因';
  return new Error(`无法连接到 ${target || 'API 服务'}：${reason}（请检查网络、Base URL 与代理设置）`);
}

/* ---------------- 400/422 参数自动兼容回退（v2） ---------------- */

/**
 * 按错误文本关键词决定回退动作（同一请求最多重试 2 次，优先级：
 * stream_options → max_tokens(改用 max_completion_tokens) → temperature）。
 * @returns {string} 已应用的回退动作描述；空串表示无可用的回退
 */
function applyOpenaiFallback(errText, flags) {
  if (!flags.noStreamOptions && /stream_options/i.test(errText)) {
    flags.noStreamOptions = true;
    return '去掉 stream_options 重试';
  }
  if (!flags.useMaxCompletionTokens && /max_tokens/i.test(errText)) {
    flags.useMaxCompletionTokens = true;
    return '改用 max_completion_tokens 重试';
  }
  if (!flags.noTemperature && /temperature/i.test(errText)) {
    flags.noTemperature = true;
    return '去掉 temperature 重试';
  }
  return '';
}

/**
 * 调用 LLM 并流式返回
 * @param {object} opts { provider, model, system, messages:[{role,content}], temperature, maxTokens, onDelta, signal }
 * @returns {{ text: string, usage: { promptTokens, completionTokens }, latency: number }} latency=开始到流结束的毫秒（v3）
 */
async function chatCompletion(opts) {
  // v3.6 停滞看门狗：串联外部 signal + 45s 无输出自动中止（避免请求挂起导致无回复）
  const outer = opts.signal;
  const ctrl = new AbortController();
  let stall = setTimeout(() => ctrl.abort(new Error('回复超时（45 秒无响应）')), 45000);
  const bump = () => { clearTimeout(stall); stall = setTimeout(() => ctrl.abort(new Error('回复超时（45 秒无响应）')), 45000); };
  const onOuterAbort = () => ctrl.abort(outer && outer.reason);
  if (outer) {
    if (outer.aborted) ctrl.abort(outer && outer.reason);
    else outer.addEventListener('abort', onOuterAbort);
  }
  try {
    const wrapped = Object.assign({}, opts, { signal: ctrl.signal, onDelta: (d) => { bump(); (opts.onDelta || function () {})(d); } });
    return await chatCompletionInner(wrapped);
  } catch (e) {
    throw hideKey(e, opts.provider);
  } finally {
    clearTimeout(stall);
    if (outer) outer.removeEventListener('abort', onOuterAbort);
  }
}

async function chatCompletionInner({ provider, model, system, messages, temperature = 0.8, maxTokens = 1024, structured = false, onDelta, signal }) {
  const started = Date.now();
  if (signal?.aborted) throw signal.reason || new DOMException('已取消', 'AbortError');
  if (!provider) throw new Error('未配置可用的 API 服务商，请在「设置 → API 服务商」中添加');
  if (provider.type === 'demo') {
    const text = rand(DEMO_REPLIES);
    await demoStream(text, onDelta, signal);
    return {
      text,
      usage: { promptTokens: estimateTokens(system + JSON.stringify(messages)), completionTokens: estimateTokens(text) },
      latency: Date.now() - started,
    };
  }
  if (provider.type === 'anthropic') return anthropicChat({ provider, model, system, messages, temperature, maxTokens, onDelta, signal, started });
  return openaiChat({ provider, model, system, messages, temperature, maxTokens, structured, onDelta, signal, started });
}

async function openaiChat({ provider, model, system, messages, temperature, maxTokens, structured, onDelta, signal, started = Date.now() }) {
  const base = normalizeBaseUrl(provider.baseUrl);
  if (!base) throw new Error(`服务商「${provider.name}」未填写 Base URL`);
  const proxyUrl = systemProxy();
  const buildBody = (flags) => {
    const body = {
      model,
      messages: [{ role: 'system', content: system }, ...messages],
      stream: true,
    };
    // DeepSeek enables reasoning by default. Short structured life decisions
    // need their saved output budget for the executable JSON response.
    // https://api-docs.deepseek.com/api/create-chat-completion/
    if (structured && new URL(base).hostname === 'api.deepseek.com' && /^deepseek-(?:v4-(?:flash|pro)|flash)$/.test(model)) {
      body.thinking = { type: 'disabled' };
      body.response_format = { type: 'json_object' };
    }
    if (!flags.noTemperature) body.temperature = temperature;
    if (flags.useMaxCompletionTokens) body.max_completion_tokens = maxTokens;
    else body.max_tokens = maxTokens;
    if (!flags.noStreamOptions) body.stream_options = { include_usage: true };
    return body;
  };
  // 回退标记：命中 400/422 关键词后逐项修改参数重试
  const flags = { noStreamOptions: false, useMaxCompletionTokens: false, noTemperature: false };
  let attempt = 0;
  while (true) {
    let res;
    try {
      res = await proxyAwareFetch(base + '/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(provider.apiKey ? { Authorization: `Bearer ${provider.apiKey}` } : {}),
        },
        body: JSON.stringify(buildBody(flags)),
        signal,
      });
    } catch (e) {
      throw readableNetworkError(e, base);
    }
    if (!res.ok) {
      // 流式请求失败：先读走 body，再决定是否用修改后的参数重试
      const t = await res.text().catch(() => '');
      const msg = extractApiError(res.status, t, provider.name);
      if (attempt < 2 && (res.status === 400 || res.status === 422)) {
        const action = applyOpenaiFallback(msg, flags);
        if (action) {
          attempt += 1;
          continue;
        }
      }
      // v3.7 中转站过载（503）或限流（429）：自动等待重试，最多 2 次
      if (attempt < 2 && (res.status === 503 || res.status === 429)) {
        attempt += 1;
        await pause(2500 * attempt, signal);
        continue;
      }
      throw new Error(msg);
    }
    let full = '', usage = null, finishReason = null, reasoningOnly = false;
    await readSSE(res.body, j => {
      const delta = j.choices?.[0]?.delta?.content;
      if (delta) { full += delta; onDelta && onDelta(delta); }
      if (j.choices?.[0]?.delta?.reasoning_content) reasoningOnly = true;
      if (j.choices?.[0]?.finish_reason) finishReason = j.choices[0].finish_reason;
      if (j.usage) usage = { promptTokens: j.usage.prompt_tokens, completionTokens: j.usage.completion_tokens };
    });
    if (!full) throw new Error('API 返回了空回复' + (finishReason === 'length' ? '（达到输出 token 上限，未生成可执行回复）' : reasoningOnly ? '（仅收到推理内容，未生成可执行回复）' : ''));
    if (!usage) usage = { promptTokens: estimateTokens(system + JSON.stringify(messages)), completionTokens: estimateTokens(full) };
    return { text: full, usage, latency: Date.now() - started };
  }
}

/** v3：OpenAI 风格 content blocks → Anthropic blocks（图片 dataURL → base64 source） */
function toAnthropicContent(content) {
  if (!Array.isArray(content)) return content;
  return content.map((block) => {
    const url = block?.image_url?.url;
    if (block?.type === 'image_url' && typeof url === 'string' && url.startsWith('data:')) {
      const m = url.match(/^data:([^;]+);base64,(.*)$/);
      if (m) return { type: 'image', source: { type: 'base64', media_type: m[1], data: m[2] } };
      return { type: 'text', text: '（一张图片，格式不支持）' };
    }
    if (block?.type === 'text') return { type: 'text', text: String(block.text || '') };
    return { type: 'text', text: JSON.stringify(block).slice(0, 200) };
  });
}

async function anthropicChat({ provider, model, system, messages, temperature, maxTokens, onDelta, signal, started = Date.now() }) {
  const base = normalizeBaseUrl(provider.baseUrl || 'https://api.anthropic.com');
  const proxyUrl = systemProxy();
  let res;
  try {
    res = await proxyAwareFetch(anthropicUrl(provider, 'messages'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': provider.apiKey || '',
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model,
        system,
        max_tokens: maxTokens,
        temperature,
        stream: true,
        messages: messages.map((m) => ({ role: m.role, content: toAnthropicContent(m.content) })),
      }),
      signal,
    });
  } catch (e) {
    throw readableNetworkError(e, base);
  }
  if (!res.ok && (res.status === 503 || res.status === 429)) {
    // v3.7 中转站过载/限流：等 3 秒重试一次
    await pause(3000, signal);
    try {
      res = await proxyAwareFetch(anthropicUrl(provider, 'messages'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': provider.apiKey || '',
          'anthropic-version': '2023-06-01',
        },
        body: JSON.stringify({
          model,
          system,
          max_tokens: maxTokens,
          temperature,
          stream: true,
          messages: messages.map((m) => ({ role: m.role, content: toAnthropicContent(m.content) })),
        }),
        signal,
      });
    } catch (e) { if (signal?.aborted) throw signal.reason || e; /* 重试失败按原错误抛出 */ }
  }
  if (!res.ok) {
    const t = await res.text().catch(() => '');
    throw new Error(extractApiError(res.status, t, provider.name));
  }
  let full = '', usage = { promptTokens: 0, completionTokens: 0 };
  await readSSE(res.body, j => {
    if (j.type === 'content_block_delta' && j.delta?.text) {
      full += j.delta.text;
      onDelta && onDelta(j.delta.text);
    } else if (j.type === 'message_start' && j.message?.usage) {
      usage.promptTokens = j.message.usage.input_tokens || 0;
    } else if (j.type === 'message_delta' && j.usage) {
      usage.completionTokens = j.usage.output_tokens || usage.completionTokens;
    }
  });
  if (!full) throw new Error('API 返回了空回复');
  if (!usage.completionTokens) usage.completionTokens = estimateTokens(full);
  if (!usage.promptTokens) usage.promptTokens = estimateTokens(system + JSON.stringify(messages));
  return { text: full, usage, latency: Date.now() - started };
}

/**
 * 获取服务商可用模型列表（v2）
 * - openai 兼容：GET {base}/models（Bearer）
 * - anthropic：GET {base}/v1/models（x-api-key + anthropic-version）
 * @returns {{ ok: boolean, models: string[], error?: string }}
 */
async function fetchModels(provider) {
  const ctrl = new AbortController();
  const timeout = setTimeout(() => ctrl.abort(new Error('模型列表请求超时（15 秒）')), 15000);
  try {
    const result = await fetchModelsInner(provider, ctrl.signal);
    if (result.error && provider?.apiKey) result.error = result.error.replaceAll(provider.apiKey, '[已隐藏]');
    return result;
  } finally { clearTimeout(timeout); }
}

async function fetchModelsInner(provider, signal) {
  const providerName = (provider && provider.name) || '未知服务商';
  try {
    const proxyUrl = systemProxy();
      if (!provider || typeof provider !== 'object') return { ok: false, models: [], error: '参数缺少 provider' };
    if (provider.type === 'demo') return { ok: true, models: ['demo'] };
    if (provider.type === 'anthropic') {
      const base = normalizeBaseUrl(provider.baseUrl || 'https://api.anthropic.com');
      let res;
      try {
        res = await proxyAwareFetch(anthropicUrl(provider, 'models'), {
          headers: {
            'x-api-key': provider.apiKey || '',
            'anthropic-version': '2023-06-01',
          },
          signal,
        });
      } catch (e) {
        const err = readableNetworkError(e, base);
        return { ok: false, models: [], error: err.message };
      }
      if (!res.ok) {
        const t = await res.text().catch(() => '');
        return { ok: false, models: [], error: extractApiError(res.status, t, providerName) };
      }
      const j = await res.json().catch(() => null);
      const models = (Array.isArray(j && j.data) ? j.data : [])
        .map((m) => m && m.id)
        .filter((x) => typeof x === 'string' && x);
      return { ok: true, models };
    }
    // openai 兼容协议
    const base = normalizeBaseUrl(provider.baseUrl);
    if (!base) return { ok: false, models: [], error: `服务商「${providerName}」未填写 Base URL` };
    let res;
    try {
      res = await proxyAwareFetch(base + '/models', {
        headers: {
          ...(provider.apiKey ? { Authorization: `Bearer ${provider.apiKey}` } : {}),
        },
        signal,
      });
    } catch (e) {
      const err = readableNetworkError(e, base);
      return { ok: false, models: [], error: err.message };
    }
    if (!res.ok) {
      const t = await res.text().catch(() => '');
      return { ok: false, models: [], error: extractApiError(res.status, t, providerName) };
    }
    const j = await res.json().catch(() => null);
    // 标准格式 { data: [{id}] }；个别兼容端点直接返回 [{id}] 或 ['model-id']
    let list = [];
    if (Array.isArray(j && j.data)) list = j.data;
    else if (Array.isArray(j)) list = j;
    const models = list
      .map((m) => (typeof m === 'string' ? m : m && m.id))
      .filter((x) => typeof x === 'string' && x);
    return { ok: true, models };
  } catch (e) {
    return { ok: false, models: [], error: String((e && e.message) || e) };
  }
}

/** 测试服务商连通性 */
async function testProvider(provider, model) {
  const started = Date.now();
  try {
    const { text } = await chatCompletion({
      provider,
      model: model || (provider.models && provider.models[0]) || 'demo',
      system: '你是一个连通性测试程序，请只回复：pong',
      messages: [{ role: 'user', content: 'ping' }],
      maxTokens: 16,
      temperature: 0,
    });
    return { ok: true, latency: Date.now() - started, text: (text || '').slice(0, 50) };
  } catch (e) {
    return { ok: false, latency: Date.now() - started, error: String(e.message || e) };
  }
}

module.exports = { chatCompletion, testProvider, fetchModels, estimateTokens, DEMO_PROACTIVE, DEMO_MOMENTS };
