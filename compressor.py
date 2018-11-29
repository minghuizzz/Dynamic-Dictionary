import math
import os
import shutil
import sys


class Encoder:
    dic = {}
    reversed_dic = {}
    size = 64000
    update = 'fc'
    delete = 'freeze'
    lru_dic = None

    def __init__(self, size=64000, update='fc', delete='freeze'):
        self.dic.clear()
        self.reversed_dic.clear()
        self.update = update
        self.delete = delete
        if size > 256:
            self.size = size
        for i in range(256):
            self.dic[chr(i)] = i
        if delete == 'lru':
            self.lru_dic = LRUDict(self.size)

    def encode(self, target_filename, compressed_filename):
        compressed_file = open(compressed_filename, 'wb')
        target_file = open(target_filename, 'r', encoding='latin-1')
        text = target_file.read()

        start = 0
        current_match = ''
        while start < len(text):

            word = text[start]
            while word in self.dic:
                start += 1
                if start >= len(text):
                    break
                word += text[start]

            previous_match = current_match
            current_match = word[:-1] if start < len(text) else word
            index = self.dic[current_match]

            byte = math.ceil(math.log(len(self.dic), 2) / 8)
            compressed_file.write(index.to_bytes(byte, 'big'))

            if self.update == 'cm':
                Update.cm_en(self, previous_match, current_match)
            else:
                Update.fc_en(self, previous_match, current_match)

        target_file.close()
        compressed_file.close()


class Decoder:
    dic = {}
    reversed_dic = {}
    size = 64000
    update = 'fc'
    delete = 'freeze'
    lru_dic = None

    def __init__(self, size=64000, update='fc', delete='freeze'):
        self.dic.clear()
        self.reversed_dic.clear()
        self.update = update
        self.delete = delete
        if size > 256:
            self.size = size
        for i in range(256):
            self.dic[chr(i)] = i
            self.reversed_dic[i] = chr(i)
        if delete == 'lru':
            self.lru_dic = LRUDict(self.size)

    def decode(self, compressed_filename, decompressed_filename):
        compressed_file = open(compressed_filename, 'rb')
        decompressed_file = open(decompressed_filename, 'w', encoding='latin-1')

        current_match = ''
        bi = compressed_file.read(1)
        while bi:
            index = int.from_bytes(bi, 'big')
            previous_match = current_match
            current_match = self.reversed_dic[index]
            decompressed_file.write(current_match)

            if self.update == 'cm':
                Update.cm_de(self, previous_match, current_match)
            else:
                Update.fc_de(self, previous_match, current_match)

            byte = math.ceil(math.log(len(self.dic), 2) / 8)
            bi = compressed_file.read(byte)

        compressed_file.close()
        decompressed_file.close()


class Node:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class LRUDict:
    def __init__(self, capacity):
        self.capacity = capacity
        self.dic = {}
        self.head = Node(0, 0)
        self.tail = Node(0, 0)
        self.head.next = self.tail
        self.tail.prev = self.head

    def get(self, key):
        if key in self.dic:
            node = self.dic[key]
            self._remove(node)
            self._add(node)
            return node.value
        return -1

    def put(self, key, value):
        deleted_node = None
        if key in self.dic:
            node = self.dic[key]
            self._remove(node)
            self._add(node)
        else:
            node = Node(key, value)

            if len(self.dic) >= self.capacity:
                deleted_node = self.head.next
                node.value = deleted_node.value
                self.dic.pop(deleted_node.key)
                self._remove(deleted_node)

            self._add(node)
            self.dic[key] = node

        return deleted_node

    def _remove(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def _add(self, node):
        prev = self.tail.prev
        prev.next = node
        node.prev = prev
        node.next = self.tail
        self.tail.prev = node


class Update:
    @staticmethod
    def fc_en(encoder, previous_match, current_match):
        new_word = previous_match + current_match[0]
        Update.update_en(encoder, new_word)

    @staticmethod
    def fc_de(decoder, previous_match, current_match):
        new_word = previous_match + current_match[0]
        Update.update_de(decoder, new_word)

    @staticmethod
    def cm_en(encoder, previous_match, current_match):
        new_word = previous_match + current_match
        Update.update_en(encoder, new_word)

    @staticmethod
    def cm_de(decoder, previous_match, current_match):
        new_word = previous_match + current_match
        Update.update_de(decoder, new_word)

    @staticmethod
    def update_en(encoder, new_word):
        if encoder.delete == 'lru':
            if new_word in encoder.dic:
                encoder.lru_dic.get(new_word)
                if len(new_word) > 2:
                    for i in range(len(new_word) - 2):
                        index = -i - 1
                        encoder.lru_dic.get(new_word[:index])
            else:
                deleted_node = encoder.lru_dic.put(new_word, len(encoder.dic))
                if deleted_node is not None:
                    encoder.dic.pop(deleted_node.key)
                    encoder.dic[new_word] = deleted_node.value
                else:
                    encoder.dic[new_word] = len(encoder.dic)
            return
        if new_word not in encoder.dic:
            if len(encoder.dic) >= encoder.size:
                if encoder.delete == 'freeze':
                    Deletion.freeze_en(encoder)
                elif encoder.delete == 'restart':
                    Deletion.restart_en(encoder)
                    encoder.dic[new_word] = len(encoder.dic)
            else:
                encoder.dic[new_word] = len(encoder.dic)

    @staticmethod
    def update_de(decoder, new_word):
        if decoder.delete == 'lru':
            if new_word in decoder.dic:
                decoder.lru_dic.get(new_word)
                if len(new_word) > 2:
                    for i in range(len(new_word) - 2):
                        index = -i - 1
                        decoder.lru_dic.get(new_word[:index])
            else:
                deleted_node = decoder.lru_dic.put(new_word, len(decoder.dic))
                if deleted_node is not None:
                    decoder.dic.pop(deleted_node.key)
                    decoder.dic[new_word] = deleted_node.value
                    decoder.reversed_dic[deleted_node.value] = new_word
                else:
                    decoder.dic[new_word] = len(decoder.dic)
                    decoder.reversed_dic[len(decoder.reversed_dic)] = new_word
            return
        if new_word not in decoder.dic:
            if len(decoder.dic) >= decoder.size:
                if decoder.delete == 'freeze':
                    Deletion.freeze_de(decoder)
                elif decoder.delete == 'restart':
                    Deletion.restart_de(decoder)
                    decoder.dic[new_word] = len(decoder.dic)
                    decoder.reversed_dic[len(decoder.reversed_dic)] = new_word
            else:
                decoder.dic[new_word] = len(decoder.dic)
                decoder.reversed_dic[len(decoder.reversed_dic)] = new_word


class Deletion:
    @staticmethod
    def freeze_en(encoder):
        pass

    @staticmethod
    def freeze_de(decoder):
        pass

    @staticmethod
    def restart_en(encoder):
        if len(encoder.dic) >= encoder.size:
            new_dic = {}
            for i in range(256):
                new_dic[chr(i)] = i
            encoder.dic = new_dic

    @staticmethod
    def restart_de(decoder):
        if len(decoder.dic) >= decoder.size:
            new_dic = {}
            new_reversed_dic = {}
            for i in range(256):
                new_dic[chr(i)] = i
                new_reversed_dic[i] = chr(i)
            decoder.dic = new_dic
            decoder.reversed_dic = new_reversed_dic


if __name__ == '__main__':
    update = 'cm'
    delete = 'freeze'
    file_name = None
    dict_size = 4000
    for arg in sys.argv:
        if arg.__contains__('.py'):
            pass
        elif arg.__contains__('update='):
            update = arg.replace('update=', '')
        elif arg.__contains__('delete='):
            delete = arg.replace('delete=', '')
        elif arg.__contains__('file_name='):
            file_name = arg.replace('file_name=', '')
        elif arg.__contains__('dict_size='):
            dict_size = arg.replace('dict_size=', '')
        else:
            print('Usage: python compressor.py [update=] [delete=] [file_name=] [dict_size=]')
            print('options: update=fc/cm, delete=freeze/restart/lru')
            print('         file_name=file under test_files with the end .txt')
            print('         dict_size=number > 256')
            print('e.g. python compressor.py update=fc delete=lru file_name=bib.txt dict_size=64000')
            exit(1)

    if os.path.exists('compressed_files_4k'):
        shutil.rmtree('compressed_files_4k')
    os.makedirs('compressed_files_4k')

    if os.path.exists('decompressed_files'):
        shutil.rmtree('decompressed_files')
    os.makedirs('decompressed_files')

    if file_name is None:
        files = os.listdir('test_files')
    else:
        files = [file_name]

    for filename in files:
        if filename.endswith('.txt'):
            target_filename = 'test_files/' + filename
            compressed_filename = 'compressed_files_4k/' + filename.replace('.txt', '')
            decompressed_filename = 'decompressed_files/' + filename.replace('.txt', '_de.txt')
            e = Encoder(size=dict_size, update=update, delete=delete)
            print("Encoding " + filename + "...")
            e.encode(target_filename, compressed_filename)

            d = Decoder(size=dict_size, update=update, delete=delete)
            print("Decoding " + filename + "...")
            d.decode(compressed_filename, decompressed_filename)







