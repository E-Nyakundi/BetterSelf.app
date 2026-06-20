/* ==========================================================================
   Live media capture
   Progressively enhances `<input type="file">` fields into tap-to-record
   controls: tap the camera to snap a live photo, tap again to film a clip,
   tap the mic to record audio right in the browser. The underlying file
   input still exists and still submits normally — this just fills it with
   a real File built from the camera/mic stream instead of asking the user
   to leave the page. If the browser can't do live capture (no permission,
   no HTTPS, old browser), everything quietly falls back to the native
   file picker that was already there.
   ========================================================================== */
(function () {
    'use strict';

    var fields = document.querySelectorAll('.capture-field');
    if (!fields.length) return;

    function supportsMedia() {
        return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    }

    function fileFromBlob(blob, filename) {
        try {
            return new File([blob], filename, { type: blob.type });
        } catch (e) {
            return blob;
        }
    }

    function assignToInput(input, file) {
        try {
            var dt = new DataTransfer();
            dt.items.add(file);
            input.files = dt.files;
            input.dispatchEvent(new Event('change', { bubbles: true }));
            return true;
        } catch (e) {
            return false;
        }
    }

    function formatTime(totalSeconds) {
        var m = Math.floor(totalSeconds / 60);
        var s = Math.floor(totalSeconds % 60);
        return (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
    }

    function stopStream(stream) {
        if (stream) {
            stream.getTracks().forEach(function (track) { track.stop(); });
        }
    }

    function pickRecorderMime(candidates) {
        if (!window.MediaRecorder) return '';
        for (var i = 0; i < candidates.length; i++) {
            if (MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(candidates[i])) {
                return candidates[i];
            }
        }
        return '';
    }

    function setPreview(field, url, kind, onRemove) {
        var preview = field.querySelector('[data-role="preview"]');
        if (!preview) return;
        preview.innerHTML = '';
        var el;
        if (kind === 'image') {
            el = document.createElement('img');
            el.src = url;
            el.alt = 'Captured photo';
        } else if (kind === 'video') {
            el = document.createElement('video');
            el.src = url;
            el.controls = true;
            el.playsInline = true;
        } else if (kind === 'audio') {
            el = document.createElement('audio');
            el.src = url;
            el.controls = true;
        }
        if (!el) return;
        el.className = 'capture-preview-media';
        preview.appendChild(el);

        var removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'capture-preview-remove';
        removeBtn.setAttribute('aria-label', 'Remove');
        removeBtn.innerHTML = '<i class="fa-solid fa-xmark"></i>';
        removeBtn.addEventListener('click', function () {
            preview.innerHTML = '';
            preview.classList.remove('has-media');
            if (onRemove) onRemove();
        });
        preview.appendChild(removeBtn);
        preview.classList.add('has-media', 'capture-pop-in');
        window.setTimeout(function () { preview.classList.remove('capture-pop-in'); }, 320);
    }

    function isCapacitorNative() {
        return !!(window.Capacitor && window.Capacitor.isNativePlatform && window.Capacitor.isNativePlatform());
    }

    function dataUrlToFile(dataUrl, filename) {
        var parts = dataUrl.split(',');
        var mimeMatch = parts[0].match(/:(.*?);/);
        var mime = mimeMatch ? mimeMatch[1] : 'image/jpeg';
        var binary = atob(parts[1]);
        var len = binary.length;
        var bytes = new Uint8Array(len);
        for (var i = 0; i < len; i++) bytes[i] = binary.charCodeAt(i);
        return fileFromBlob(new Blob([bytes], { type: mime }), filename);
    }

    // When running inside the Capacitor shell, use the real native camera
    // instead of the browser's getUserMedia overlay — this is what fixes
    // the low-resolution/disorienting preview you'd get from a WebView.
    function openNativeCamera(onCapture) {
        var Camera = window.Capacitor.Plugins.Camera;
        Camera.getPhoto({
            quality: 90,
            resultType: 'dataUrl',
            source: 'CAMERA',
            saveToGallery: false
        }).then(function (photo) {
            var dataUrl = photo.dataUrl;
            var file = dataUrlToFile(dataUrl, 'photo-' + Date.now() + '.jpeg');
            onCapture(file, dataUrl, 'image');
        }).catch(function () {
            // user cancelled, or permission denied — leave the field as-is
        });
    }

    // ---- Camera overlay (web fallback — used in regular mobile/desktop browsers) ----
    var activeOverlay = null;

    function closeOverlay(overlay, stream) {
        stopStream(stream);
        if (overlay && overlay.parentNode) {
            overlay.classList.remove('is-open');
            window.setTimeout(function () {
                if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
            }, 200);
        }
        if (activeOverlay === overlay) activeOverlay = null;
    }

    function openCamera(mode, onCapture) {
        if (activeOverlay) return;

        var overlay = document.createElement('div');
        overlay.className = 'capture-overlay';
        overlay.innerHTML =
            '<div class="capture-overlay-card">' +
                '<button type="button" class="capture-overlay-close" aria-label="Close camera"><i class="fa-solid fa-xmark"></i></button>' +
                '<div class="capture-overlay-frame">' +
                    '<video class="capture-overlay-video" autoplay playsinline muted></video>' +
                    '<span class="capture-overlay-timer" hidden>00:00</span>' +
                '</div>' +
                '<div class="capture-overlay-controls">' +
                    '<p class="capture-overlay-hint">' + (mode === 'video' ? 'Tap to start recording' : 'Tap to snap a photo') + '</p>' +
                    '<button type="button" class="capture-shutter" aria-label="Capture"><span></span></button>' +
                '</div>' +
            '</div>';
        document.body.appendChild(overlay);
        activeOverlay = overlay;
        window.requestAnimationFrame(function () { overlay.classList.add('is-open'); });

        var videoEl = overlay.querySelector('.capture-overlay-video');
        var shutter = overlay.querySelector('.capture-shutter');
        var closeBtn = overlay.querySelector('.capture-overlay-close');
        var hint = overlay.querySelector('.capture-overlay-hint');
        var timerEl = overlay.querySelector('.capture-overlay-timer');

        var constraints = mode === 'video'
            ? { video: { facingMode: 'environment', width: { ideal: 1920 }, height: { ideal: 1920 } }, audio: true }
            : { video: { facingMode: 'environment', width: { ideal: 1920 }, height: { ideal: 1920 } } };

        navigator.mediaDevices.getUserMedia(constraints).then(function (stream) {
            videoEl.srcObject = stream;

            var recorder = null;
            var chunks = [];
            var isRecording = false;
            var timerInterval = null;
            var startedAt = 0;

            closeBtn.addEventListener('click', function () {
                if (timerInterval) window.clearInterval(timerInterval);
                if (recorder && isRecording) recorder.stop();
                closeOverlay(overlay, stream);
            });

            if (mode === 'photo') {
                shutter.addEventListener('click', function () {
                    var canvas = document.createElement('canvas');
                    canvas.width = videoEl.videoWidth || 720;
                    canvas.height = videoEl.videoHeight || 720;
                    canvas.getContext('2d').drawImage(videoEl, 0, 0, canvas.width, canvas.height);
                    canvas.toBlob(function (blob) {
                        if (!blob) return;
                        var file = fileFromBlob(blob, 'photo-' + Date.now() + '.jpg');
                        onCapture(file, URL.createObjectURL(blob), 'image');
                        closeOverlay(overlay, stream);
                    }, 'image/jpeg', 0.9);
                });
            } else {
                var mime = pickRecorderMime(['video/webm;codecs=vp8,opus', 'video/webm', 'video/mp4']);
                shutter.addEventListener('click', function () {
                    if (!isRecording) {
                        chunks = [];
                        try {
                            recorder = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
                        } catch (e) {
                            recorder = new MediaRecorder(stream);
                        }
                        recorder.ondataavailable = function (e) { if (e.data && e.data.size) chunks.push(e.data); };
                        recorder.onstop = function () {
                            var blob = new Blob(chunks, { type: recorder.mimeType || 'video/webm' });
                            var ext = (recorder.mimeType || '').indexOf('mp4') > -1 ? 'mp4' : 'webm';
                            var file = fileFromBlob(blob, 'video-' + Date.now() + '.' + ext);
                            onCapture(file, URL.createObjectURL(blob), 'video');
                            closeOverlay(overlay, stream);
                        };
                        recorder.start();
                        isRecording = true;
                        startedAt = Date.now();
                        overlay.classList.add('is-recording');
                        hint.textContent = 'Tap to stop recording';
                        timerEl.hidden = false;
                        timerInterval = window.setInterval(function () {
                            timerEl.textContent = formatTime((Date.now() - startedAt) / 1000);
                        }, 250);
                    } else {
                        isRecording = false;
                        if (timerInterval) window.clearInterval(timerInterval);
                        recorder.stop();
                    }
                });
            }
        }).catch(function () {
            closeOverlay(overlay, null);
        });
    }

    // ---- Inline audio recorder (no overlay needed) ----
    function wireAudioRecorder(triggerBtn, input, field) {
        var recorder = null;
        var chunks = [];
        var stream = null;
        var isRecording = false;
        var timerInterval = null;
        var startedAt = 0;
        var labelEl = triggerBtn.querySelector('[data-role="label"]');
        var timeEl = triggerBtn.querySelector('[data-role="time"]');
        var baseLabel = labelEl ? labelEl.textContent : 'Record audio';

        triggerBtn.addEventListener('click', function () {
            if (isRecording) {
                isRecording = false;
                if (timerInterval) window.clearInterval(timerInterval);
                recorder.stop();
                return;
            }

            navigator.mediaDevices.getUserMedia({ audio: true }).then(function (mediaStream) {
                stream = mediaStream;
                chunks = [];
                var mime = pickRecorderMime(['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4']);
                try {
                    recorder = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
                } catch (e) {
                    recorder = new MediaRecorder(stream);
                }
                recorder.ondataavailable = function (e) { if (e.data && e.data.size) chunks.push(e.data); };
                recorder.onstop = function () {
                    var blob = new Blob(chunks, { type: recorder.mimeType || 'audio/webm' });
                    var ext = (recorder.mimeType || '').indexOf('mp4') > -1 ? 'm4a' : 'webm';
                    var file = fileFromBlob(blob, 'audio-' + Date.now() + '.' + ext);
                    assignToInput(input, file);
                    setPreview(field, URL.createObjectURL(blob), 'audio', function () {
                        try { var dt = new DataTransfer(); input.files = dt.files; } catch (e) {}
                    });
                    stopStream(stream);
                    triggerBtn.classList.remove('is-recording');
                    if (labelEl) labelEl.textContent = baseLabel;
                    if (timeEl) timeEl.hidden = true;
                };
                recorder.start();
                isRecording = true;
                startedAt = Date.now();
                triggerBtn.classList.add('is-recording');
                if (labelEl) labelEl.textContent = 'Tap to stop';
                if (timeEl) { timeEl.hidden = false; timeEl.textContent = '00:00'; }
                timerInterval = window.setInterval(function () {
                    if (timeEl) timeEl.textContent = formatTime((Date.now() - startedAt) / 1000);
                }, 250);
            }).catch(function () {
                input.click();
            });
        });
    }

    function initField(field) {
        var mode = field.getAttribute('data-capture'); // photo | video | audio
        var input = field.querySelector('input[type="file"]');
        if (!input) return;

        input.addEventListener('change', function () {
            var file = input.files && input.files[0];
            if (!file) return;
            var url = URL.createObjectURL(file);
            var kind = mode === 'audio' ? 'audio' : (mode === 'video' ? 'video' : 'image');
            setPreview(field, url, kind, function () {
                try { var dt = new DataTransfer(); input.files = dt.files; } catch (e) {}
            });
        });

        var triggerBtn = field.querySelector('[data-action]');
        if (!triggerBtn) return;

        var hasNativeCamera = mode === 'photo' && isCapacitorNative() && window.Capacitor.Plugins && window.Capacitor.Plugins.Camera;

        if (!hasNativeCamera && !supportsMedia()) {
            triggerBtn.addEventListener('click', function () { input.click(); });
            return;
        }

        if (mode === 'photo' || mode === 'video') {
            triggerBtn.addEventListener('click', function () {
                var onCapture = function (file, url, kind) {
                    assignToInput(input, file);
                    setPreview(field, url, kind, function () {
                        try { var dt = new DataTransfer(); input.files = dt.files; } catch (e) {}
                    });
                };
                if (hasNativeCamera) {
                    openNativeCamera(onCapture);
                } else {
                    openCamera(mode, onCapture);
                }
            });
        } else if (mode === 'audio') {
            if (!window.MediaRecorder) {
                triggerBtn.addEventListener('click', function () { input.click(); });
                return;
            }
            wireAudioRecorder(triggerBtn, input, field);
        }
    }

    fields.forEach(initField);
})();
