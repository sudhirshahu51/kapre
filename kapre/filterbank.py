# -*- coding: utf-8 -*-
from keras.engine import Layer
from keras import backend as K
from . import backend


# Todo: Filterbank(); init with mel, log, linear, etc. 
# not parameterised, just a matrix.

class Filterbank(Layer):
    '''Filterbank assumes a 2d input, i.e., ``(None, n_ch, n_freqs, n_time)`` (theano).
    
    Notes
    -----
    input_shape: ``(None, n_ch, n_freqs, n_time)``

    output_shape: ``(None, n_ch, n_mels, n_time)``
    
    Parameters
    ----------
    n_fbs: int
        Number of filterbanks

    sr: int
        sampling rate. It is used to initialize ``freq_to_mel``.

    init: str
        if ``'mel'``, init with mel center frequencies and stds.

    fmin = float
        min frequency of filterbanks.

    fmax = float
        max frequency of filterbanks.

    trainable_fb: bool,
        Whether the filterbanks are trainalbe or not.
    
    '''

    def __init__(self, n_fbs, trainable_fb, sr=None, init='mel', fmin=0., fmax=None,
                 bins_per_octave=12, **kwargs):
        ''' TODO: is sr necessary? is fmax necessary? init with None?  '''
        self.supports_masking = True
        self.n_fbs = n_fbs
        assert init in ('mel', 'log', 'linear', 'uni_random')
        if fmax is None:
            self.fmax = sr / 2.
        if init in ('mel', 'log'):
            assert sr is not None
        self.bins_per_octave = bins_per_octave
        self.sr = sr
        self.trainable_fb = trainable_fb
        super(Filterbank, self).__init__(**kwargs)

    def build(self, input_shape):
        if self.dim_ordering == 'th':
            self.n_ch = input_shape[1]
            self.n_freq = input_shape[2]
            self.n_time = input_shape[3]
        else:
            self.n_ch = input_shape[3]
            self.n_freq = input_shape[1]
            self.n_time = input_shape[2]

        if self.init == 'mel':
            self.filterbank = backend.filterbank_mel(sr=self.sr,
                                                     n_freq=self.n_freq,
                                                     n_mels=self.n_fbs,
                                                     fmin=self.fmin,
                                                     fmax=self.fmax)
        elif self.init == 'log':
            self.filterbank = backend.filterbank_log(sr=sr,
                                                     n_freq=self.n_freq,
                                                     n_bins=self.n_fbs,
                                                     bins_per_octave=self.bins_per_octave,
                                                     fmin=self.fmin)

        if self.trainable_fb == True:
            self.trainable_weights.append(self.filterbank)
        else:
            self.non_trainable_weights.append(self.filterbank)
        self.built = True

    def compute_output_shape(self, input_shape):
        if self.dim_ordering == 'th':
            return (input_shape[0], self.n_ch, self.n_fbs, self.n_time)
        else:
            return (input_shape[0], self.n_fbs, self.n_time, self.n_ch)

    def call(self, x):
        if self.dim_ordering == 'th':
            x = K.permute_dimensions(x, [0, 1, 3, 2])
        else:
            x = K.permute_dimensions(x, [0, 3, 2, 1])
        output = K.dot(x, self.filterbank)

        if self.dim_ordering == 'th':
            return K.permute_dimensions(output, [0, 1, 3, 2])
        else:
            return K.permute_dimensions(output, [0, 3, 2, 1])

    def get_config(self):
        config = {'n_fbs': self.n_fbs,
                  'sr': self.sr,
                  'init': self.init,
                  'fmin': self.fmin,
                  'fmax': self.fmax,
                  'bins_per_octave': self.bins_per_octave,
                  'trainable_fb': self.trainable_fb}
        base_config = super(Filterbank, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))
